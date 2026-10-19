"""Pure transitions. Persistence and transport live outside this module."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .models import Action, CreateSession, Event, PlanRequest


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(now: datetime) -> str:
    return now.isoformat()


class TransitionError(Exception):
    pass


def preview_plan(request: PlanRequest, catalog: dict) -> dict:
    groups = {group["id"] for group in catalog["muscle_groups"]}
    unknown = set(request.muscle_group_ids) - groups
    if unknown:
        raise TransitionError(f"Unknown muscle group: {sorted(unknown)[0]}")

    candidates: dict[str, list[dict]] = {}
    for group_id in request.muscle_group_ids:
        primary = [exercise for exercise in catalog["exercises"] if exercise["primary_muscle_group"] == group_id]
        secondary = [
            exercise for exercise in catalog["exercises"]
            if group_id in exercise["secondary_muscle_groups"] and exercise not in primary
        ]
        candidates[group_id] = primary + secondary

    chosen: list[dict] = []
    chosen_ids: set[str] = set()
    cursors = {group_id: 0 for group_id in request.muscle_group_ids}
    for _ in range(2):
        for group_id in request.muscle_group_ids:
            options = candidates[group_id]
            while cursors[group_id] < len(options) and options[cursors[group_id]]["id"] in chosen_ids:
                cursors[group_id] += 1
            if cursors[group_id] >= len(options):
                continue
            exercise = options[cursors[group_id]]
            cursors[group_id] += 1
            chosen_ids.add(exercise["id"])
            chosen.append({
                "exercise_id": exercise["id"],
                "sets": exercise["sets"],
                "reps": exercise["reps"],
                "weight_lb": None,
            })
            if len(chosen) == 8:
                return {"muscle_group_ids": request.muscle_group_ids, "plan": chosen}
    return {"muscle_group_ids": request.muscle_group_ids, "plan": chosen}


def exercise_instance(exercise: dict, *, sets: int | None = None, reps: int | None = None, weight_lb: int | None = None) -> dict:
    return {
        **deepcopy(exercise),
        "sets": sets if sets is not None else exercise["sets"],
        "reps": reps if reps is not None else exercise["reps"],
        "weight_lb": weight_lb,
        "instance_id": str(uuid4()),
        "original_exercise_id": exercise["id"],
        "completed_sets": 0,
        "set_records": [],
    }


def new_session(request: CreateSession, catalog: dict, now: datetime) -> dict:
    routine = next((r for r in catalog["routines"] if r["id"] == request.routine_id), None)
    if not routine:
        raise TransitionError("Unknown routine")
    exercises = {e["id"]: e for e in catalog["exercises"]}
    groups = {group["id"] for group in catalog["muscle_groups"]}
    excluded = set(request.preferences.excluded_exercise_ids)
    if excluded - exercises.keys():
        raise TransitionError("Unknown excluded exercise")

    queue: list[dict] = []
    if request.plan is not None:
        selected = set(request.selected_muscle_group_ids)
        unknown_groups = selected - groups
        if unknown_groups:
            raise TransitionError(f"Unknown muscle group: {sorted(unknown_groups)[0]}")
        plan_ids = [item.exercise_id for item in request.plan]
        if len(plan_ids) != len(set(plan_ids)):
            raise TransitionError("A customized plan cannot repeat a machine")
        for item in request.plan:
            exercise = exercises.get(item.exercise_id)
            if not exercise:
                raise TransitionError("Customized plan contains an unknown exercise")
            if item.exercise_id in excluded:
                raise TransitionError("Customized plan contains an excluded exercise")
            exercise_groups = {exercise["primary_muscle_group"], *exercise["secondary_muscle_groups"]}
            if selected.isdisjoint(exercise_groups):
                raise TransitionError("Customized exercise does not train a selected muscle group")
            if item.weight_lb is not None and (
                item.weight_lb < exercise["weight_min_lb"]
                or item.weight_lb > exercise["weight_max_lb"]
                or item.weight_lb % exercise["weight_step_lb"] != 0
            ):
                raise TransitionError("Selected weight is outside this machine's configured range")
            queue.append(exercise_instance(
                exercise,
                sets=item.sets,
                reps=item.reps,
                weight_lb=item.weight_lb,
            ))
    else:
        for exercise_id in routine["exercise_ids"]:
            if exercise_id not in excluded:
                queue.append(exercise_instance(exercises[exercise_id]))
    if not queue:
        raise TransitionError("Preferences exclude every exercise in this routine")
    current = queue.pop(0)
    return {
        "schema_version": 1, "session_id": str(uuid4()), "version": 1,
        "server_time": stamp(now), "created_at": stamp(now), "ended_at": None,
        "phase": "awaiting_equipment", "preferences": request.preferences.model_dump(),
        "demo_mode": request.demo_mode, "current": current, "set_index": 1,
        "rest_deadline": None, "set_started_at": None, "queue": queue, "deferred": [], "completed": [], "skipped": [],
        "pending_alternative": None, "last_decision": f"Start with {current['name']}. Confirm when you have the equipment.",
    }


def next_exercise(state: dict) -> None:
    state["rest_deadline"] = None
    state["set_started_at"] = None
    state["pending_alternative"] = None
    state["set_index"] = 1
    if state["queue"]:
        state["current"] = state["queue"].pop(0)
        state["phase"] = "awaiting_equipment"
        state["last_decision"] = f"Next: {state['current']['name']}. Confirm when you have the equipment."
    elif state["deferred"]:
        state["current"] = None
        state["phase"] = "blocked"
        state["last_decision"] = "Your remaining exercises were reported taken. Retry them, skip them individually, or end today."
    else:
        state["current"] = None
        state["phase"] = "completed"
        state["ended_at"] = state["server_time"]
        state["last_decision"] = "Workout complete. Your actual completed sets are saved."


def expire_rest(state: dict, now: datetime) -> bool:
    if state["phase"] != "resting" or not state["rest_deadline"]:
        return False
    if datetime.fromisoformat(state["rest_deadline"]) > now:
        return False
    state["phase"] = "exercising"
    # Start at the persisted deadline, even if the restart/timer check is late.
    state["set_started_at"] = state["rest_deadline"]
    state["rest_deadline"] = None
    state["version"] += 1
    state["server_time"] = stamp(now)
    state["last_decision"] = f"Rest finished. Ready for set {state['set_index']} of {state['current']['name']}."
    return True


def transition(original: dict, event: Event, catalog: dict, now: datetime) -> dict:
    state = deepcopy(original)
    state["server_time"] = stamp(now)
    if state["phase"] in {"completed", "ended"}:
        raise TransitionError("This session is finished")
    current = state["current"]
    if event.type not in {Action.END, Action.RETRY}:
        if not current or event.exercise_instance_id != current["instance_id"]:
            raise TransitionError("Action does not target the current exercise")
    if event.type == Action.END:
        state["phase"] = "ended"
        state["rest_deadline"] = None
        state["set_started_at"] = None
        state["pending_alternative"] = None
        state["ended_at"] = stamp(now)
        state["last_decision"] = "Session ended. Completed work has been saved."
    elif event.type == Action.RETRY:
        if state["phase"] != "blocked" or not state["deferred"]:
            raise TransitionError("Retry is only available when remaining exercises are blocked")
        state["queue"] = state["deferred"]
        state["deferred"] = []
        next_exercise(state)
    elif event.type == Action.CLAIM:
        if state["phase"] != "awaiting_equipment":
            raise TransitionError("Equipment confirmation is not currently expected")
        state["phase"] = "exercising"
        state["set_started_at"] = stamp(now)
        state["last_decision"] = f"Okay, machine found. Your set timer has started. {current['setup']} {current['cue']}"
    elif event.type == Action.COMPLETE:
        if state["phase"] != "exercising" or event.set_index != state["set_index"]:
            raise TransitionError("This set cannot be completed in the current phase")
        started = state.get("set_started_at")
        current.setdefault("set_records", []).append({
            "set_index": state["set_index"], "started_at": started, "completed_at": stamp(now),
            "duration_seconds": max(0.0, (now - datetime.fromisoformat(started)).total_seconds()) if started else None,
            "planned_reps": current["reps"], "weight_lb": current["weight_lb"],
        })
        state["set_started_at"] = None
        current["completed_sets"] += 1
        if current["completed_sets"] >= current["sets"]:
            state["completed"].append(current)
            next_exercise(state)
        else:
            state["set_index"] += 1
            state["phase"] = "resting"
            seconds = 5 if state["demo_mode"] else current["rest_seconds"]
            state["rest_deadline"] = stamp(now + timedelta(seconds=seconds))
            state["last_decision"] = f"Set saved. Rest for {seconds} seconds."
            weight = current["weight_lb"]
            step = current["weight_step_lb"]
            if weight is not None and step <= weight * 0.1 and weight + step <= current["weight_max_lb"]:
                state["last_decision"] += (
                    f" If those {current['reps']} planned reps at {weight} lb were comfortable and controlled,"
                    f" consider increasing by {step} lb to {weight + step} lb for the next set."
                    " Keep the same weight if unsure. Would you like to change it?"
                )
            elif weight is None:
                state["last_decision"] += " What weight are you using? Tell me before changing the next set's weight."
            else:
                state["last_decision"] += " Keep the same weight for the next set; ask a qualified trainer before making a larger increase."
    elif event.type == Action.WEIGHT:
        if state["phase"] not in {"resting", "exercising"} or event.set_index != state["set_index"]:
            raise TransitionError("Weight changes must target the current upcoming or active set")
        weight = event.payload.get("weight_lb")
        if weight is None:
            if current["weight_lb"] is None:
                raise TransitionError("Current weight is unknown. Tell Mat the new total weight in pounds")
            weight = current["weight_lb"] + event.payload["weight_increase_lb"]
        if weight < current["weight_min_lb"] or weight > current["weight_max_lb"] or weight % current["weight_step_lb"] != 0:
            raise TransitionError("Weight must match this machine's configured range and increment")
        current["weight_lb"] = weight
        state["last_decision"] = f"Weight updated to {weight} lb for set {state['set_index']} of {current['name']}."
    elif event.type == Action.SKIP:
        state["skipped"].append(current)
        next_exercise(state)
    elif event.type == Action.TAKEN:
        if state["phase"] != "awaiting_equipment":
            raise TransitionError("Report Taken before starting the exercise")
        by_id = {e["id"]: e for e in catalog["exercises"]}
        candidate = next((by_id[x] for x in current["alternatives"] if x not in state["preferences"]["excluded_exercise_ids"]), None)
        if state["preferences"]["mode"] == "alternatives" and candidate:
            state["phase"] = "awaiting_alternative_confirmation"
            state["pending_alternative"] = deepcopy(candidate)
            state["last_decision"] = f"Equipment reported taken. Would you like {candidate['name']} instead?"
        else:
            state["deferred"].append(current)
            next_exercise(state)
            if state["current"]:
                state["last_decision"] = f"Equipment reported taken. Keeping your exercises; try {state['current']['name']} next."
    elif event.type in {Action.ACCEPT, Action.DECLINE}:
        if state["phase"] != "awaiting_alternative_confirmation":
            raise TransitionError("There is no pending alternative")
        if event.type == Action.ACCEPT:
            replacement = state["pending_alternative"]
            state["current"] = {
                **replacement,
                "weight_lb": None,
                "instance_id": str(uuid4()),
                "original_exercise_id": current["original_exercise_id"],
                "completed_sets": 0,
                "set_records": [],
            }
            state["pending_alternative"] = None
            state["phase"] = "awaiting_equipment"
            state["last_decision"] = f"Alternative accepted. Confirm when you have the equipment for {replacement['name']}. Choose a suitable weight independently."
        else:
            state["deferred"].append(current)
            next_exercise(state)
    else:
        raise TransitionError("Unsupported action")
    state["version"] += 1
    return state


def summary(state: dict) -> dict:
    entries = state["completed"] + state["skipped"] + state["queue"] + state["deferred"] + ([state["current"]] if state["current"] else [])
    return {
        "session_id": state["session_id"], "phase": state["phase"],
        "completed_sets": sum(e["completed_sets"] for e in entries),
        "completed_exercises": len(state["completed"]),
        "completed": state["completed"], "skipped": state["skipped"],
        "partial": [e for e in entries if e["completed_sets"] > 0 and e not in state["completed"]],
        "substituted": [e for e in entries if e["id"] != e["original_exercise_id"]],
    }
