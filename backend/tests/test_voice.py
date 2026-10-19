import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.spotter.models import Action
from backend.spotter.tool_contract import tool_specifications


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-provider-secret")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_test")


def create(client):
    result = client.post("/sessions", json={}).json()
    return result["snapshot"], {"Authorization": f'Bearer {result["access_token"]}'}


def test_private_authorization_scoped_and_no_cache(tmp_path, configured):
    calls = []
    def provider(request):
        calls.append(request)
        assert request.url.host == "api.elevenlabs.io"
        assert request.url.path == "/v1/convai/conversation/token"
        assert dict(request.url.params) == {"agent_id": "agent_test"}
        assert request.headers["xi-api-key"] == "test-provider-secret"
        assert request.extensions["timeout"]["read"] == 10
        return httpx.Response(200, json={"token": f"ephemeral-{len(calls)}", "conversation_id": "ignored"})
    with TestClient(create_app(str(tmp_path / "voice.sqlite3"), voice_transport=httpx.MockTransport(provider))) as client:
        state, headers = create(client)
        other, _ = create(client)
        for auth in ({}, {"Authorization": "Bearer wrong"}, headers):
            sid = other["session_id"] if auth == headers else state["session_id"]
            assert client.post("/voice/token", json={"session_id": sid}, headers=auth).status_code == 401
        assert calls == []
        for index in (1, 2):
            response = client.post("/voice/token", json={"session_id": state["session_id"]}, headers=headers)
            assert response.json() == {"conversation_token": f"ephemeral-{index}"}
            assert response.headers["cache-control"] == "no-store"
        assert client.get(f'/sessions/{state["session_id"]}', headers=headers).json()["version"] == 1
        client.post(f'/sessions/{state["session_id"]}/events', headers=headers, json={
            "event_id": "00000000-0000-4000-8000-000000000002", "expected_version": 1,
            "source": "web", "type": "end_session", "exercise_instance_id": None, "set_index": None, "payload": {},
        })
        assert client.post("/voice/token", json={"session_id": state["session_id"]}, headers=headers).status_code == 409
        assert len(calls) == 2


@pytest.mark.parametrize("failure", ["401", "429", "500", "redirect", "timeout", "missing", "empty", "wrong_type", "invalid_json"])
def test_provider_errors_are_sanitized(tmp_path, configured, failure):
    def provider(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("test-provider-secret", request=request)
        if failure.isdigit():
            return httpx.Response(int(failure), text="test-provider-secret")
        if failure == "redirect":
            return httpx.Response(302, headers={"Location": "https://untrusted.invalid/secret"})
        if failure == "invalid_json":
            return httpx.Response(200, text="test-provider-secret")
        return httpx.Response(200, json={"missing": {}, "empty": {"token": " "}, "wrong_type": {"token": 42}}[failure])
    with TestClient(create_app(str(tmp_path / "error.sqlite3"), voice_transport=httpx.MockTransport(provider))) as client:
        state, headers = create(client)
        response = client.post("/voice/token", json={"session_id": state["session_id"]}, headers=headers)
        assert response.status_code == 502
        assert "test-provider-secret" not in response.text
        assert "workout buttons still work" in response.json()["detail"]
        assert client.get(f'/sessions/{state["session_id"]}', headers=headers).json()["version"] == 1


def test_missing_configuration_and_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", " ")
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    def forbidden(request):
        pytest.fail("Unconfigured authorization must not contact provider")
    with TestClient(create_app(str(tmp_path / "unconfigured.sqlite3"), voice_transport=httpx.MockTransport(forbidden))) as client:
        state, headers = create(client)
        assert client.get("/health").json()["voice_configured"] is False
        assert client.post("/voice/token", json={"session_id": state["session_id"]}, headers=headers).status_code == 503
        for body in ({"session_id": ""}, {"session_id": state["session_id"], "agent_id": "override"}):
            assert client.post("/voice/token", json=body, headers=headers).status_code == 422


def test_exported_tools_match_backend_and_client():
    root = Path(__file__).resolve().parents[2]
    tools = tool_specifications()
    assert json.loads((root / "agent/tools.json").read_text()) == tools
    assert json.loads((root / "contracts/client-tools.json").read_text()) == tools
    # Client-tool handlers are shared by the web and native provider adapters.
    client = (root / "mobile/src/voice/voice-panel-shared.tsx").read_text(encoding="utf-8")
    web_adapter = (root / "mobile/src/voice/voice-panel.web.tsx").read_text(encoding="utf-8")
    native_adapter = (root / "mobile/src/voice/voice-panel.tsx").read_text(encoding="utf-8")
    assert "VoicePanelShared" in web_adapter and "VoicePanelShared" in native_adapter
    assert "@elevenlabs/react'" in web_adapter
    assert "@elevenlabs/react-native'" in native_adapter
    for tool in tools:
        assert f'{tool["name"]}:' in client
        assert tool["wait_for_response"] is True
        assert tool["parameters"]["additionalProperties"] is False
    assert set(tools[-1]["parameters"]["properties"]["action"]["enum"]) == {action.value for action in Action}
    assert "rest_elapsed" not in tools[-1]["parameters"]["properties"]["action"]["enum"]
    assert tools[-1]["parameters"]["required"] == ["action"]


def test_optional_tool_targets_only_for_session_actions():
    from pydantic import ValidationError
    from backend.spotter.tool_contract import SubmitWorkoutAction
    for kind in ("end_session", "retry_deferred"):
        args = SubmitWorkoutAction.model_validate({"action": kind})
        assert args.exercise_instance_id is None and args.set_index is None
    for kind in ("set_completed", "equipment_claimed", "equipment_taken", "skip_exercise", "alternative_accepted", "alternative_declined"):
        with pytest.raises(ValidationError):
            SubmitWorkoutAction.model_validate({"action": kind})
