"""Canonical client-tool argument schemas; not a second tool execution engine."""
from pydantic import Field, model_validator

from .models import Action, StrictModel, WeightChange


class GetSessionState(StrictModel):
    pass


class GetExerciseGuidance(StrictModel):
    exercise_id: str = Field(min_length=1, description="Catalog exercise ID returned by the authoritative current snapshot; never an instance ID.")


class SubmitWorkoutAction(StrictModel):
    action: Action
    exercise_instance_id: str | None = Field(default=None, description="Current instance_id. Omit for end_session or retry_deferred.")
    set_index: int | None = Field(default=None, ge=1, description="Current 1-based set index. Omit for end_session or retry_deferred.")
    weight_lb: int | None = Field(default=None, ge=5, le=500, multiple_of=5, strict=True, description="Explicit user-selected new total pounds. Only for weight_updated; do not combine with an increase.")
    weight_increase_lb: int | None = Field(default=None, gt=0, le=500, multiple_of=5, strict=True, description="Explicit user-selected increase in pounds, e.g. 5 for 'increase by 5 lb'. Only for weight_updated.")

    @model_validator(mode="after")
    def require_exercise_target(self):
        if self.action not in {Action.END, Action.RETRY} and (not self.exercise_instance_id or self.set_index is None):
            raise ValueError("Exercise actions require current instance and set index")
        if self.action == Action.WEIGHT:
            WeightChange(weight_lb=self.weight_lb, weight_increase_lb=self.weight_increase_lb)
        elif self.weight_lb is not None or self.weight_increase_lb is not None:
            raise ValueError("Weight arguments are only valid for weight_updated")
        return self


TOOL_MODELS = {
    "get_session_state": (GetSessionState, "Fetch authoritative state before a workout action. Read-only."),
    "get_exercise_guidance": (GetExerciseGuidance, "Fetch curated catalog setup, cues, muscles and common mistakes. Read-only; no observed-form claims."),
    "submit_workout_action": (SubmitWorkoutAction, "Submit one explicit user-requested action and wait for success. Never retry against a new target after rejection."),
}


def tool_specifications() -> list[dict]:
    tools = []
    for name, (model, description) in TOOL_MODELS.items():
        schema = model.model_json_schema()
        definitions = schema.pop("$defs", {})
        for value in schema["properties"].values():
            reference = value.pop("$ref", None)
            if reference:
                value.update(definitions[reference.rsplit("/", 1)[1]])
        tools.append(dict(name=name, description=description, parameters=schema, wait_for_response=True))
    return tools
