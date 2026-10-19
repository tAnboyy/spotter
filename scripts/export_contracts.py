"""Regenerate API contracts from validated Pydantic models."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.spotter.models import (
    AuthResult,
    CreateResult,
    CreateSession,
    Event,
    EventResult,
    GoogleAuthRequest,
    PlanPreview,
    PlanRequest,
    PlannedExercise,
    PongFrame,
    ProfileUpdate,
    Snapshot,
    SnapshotFrame,
    StreamAuthorization,
    UserProfile,
    SetRecord,
    WeightChange,
    WeeklyWorkout,
    ScheduleUpdate,
)
from backend.app import app
from backend.spotter.voice import VoiceRequest, VoiceAuthorization
from backend.spotter.tool_contract import tool_specifications

if __name__ == "__main__":
    target = ROOT / "contracts"
    target.mkdir(exist_ok=True)
    for model in (
        CreateSession,
        Event,
        Snapshot,
        EventResult,
        CreateResult,
        VoiceRequest,
        VoiceAuthorization,
        PlannedExercise,
        PlanRequest,
        PlanPreview,
        StreamAuthorization,
        SnapshotFrame,
        PongFrame,
        GoogleAuthRequest,
        UserProfile,
        AuthResult,
        ProfileUpdate,
        SetRecord,
        WeightChange,
        WeeklyWorkout,
        ScheduleUpdate,
    ):
        (target / f"{model.__name__}.schema.json").write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
    (target / "openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
    tools = json.dumps(tool_specifications(), indent=2) + "\n"
    (target / "client-tools.json").write_text(tools)
    (ROOT / "agent/tools.json").write_text(tools)
    print("Exported schema version 1 and OpenAPI")
