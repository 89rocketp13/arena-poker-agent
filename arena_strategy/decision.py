from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .betting import Action, ActionType
from .decision_engine import DecisionEngine
from .learning import LearningStore
from .opponent_model import OpponentProfile
from .state_parser import parse_table_state


@dataclass(frozen=True)
class DecisionResponse:
    action: str
    amount: int
    message: str
    reasoning: dict


def decide_action(
    live_table_json: dict,
    opponent: OpponentProfile | None = None,
    simulations: int = 300,
    seed: int | None = None,
    use_learning: bool = True,
    call_log_path: str | Path = "arena-data/decision-calls.jsonl",
) -> DecisionResponse:
    """Return a compact action response for Hermes/live-operator use.

    This facade intentionally exposes only an already-legal action and concise
    reasoning. Heavy analysis belongs between hands, not during action deadlines.
    """

    state = parse_table_state(live_table_json)
    decision = DecisionEngine(simulations=simulations, seed=seed).decide(state, opponent)
    assert_legal_response(decision.action, state.betting_state.stack)
    learning_profile = LearningStore().load() if use_learning else None
    chosen_action = apply_learning_guard(decision.action, decision.candidates, learning_profile)
    assert_legal_response(chosen_action, state.betting_state.stack)
    top = next((candidate for candidate in decision.candidates if candidate.action == chosen_action), decision.candidates[0])
    message = f"{chosen_action.action_type.value} {chosen_action.amount}".strip()
    reasoning = {
        "equity": round(decision.context.equity, 4),
        "spr": round(decision.context.spr, 3),
        "hand_rank": decision.context.hand_rank.name if decision.context.hand_rank else "preflop",
        "board_texture": asdict(decision.context.board_texture),
        "opponent_label": decision.context.opponent_label or "unknown",
        "estimated_ev": round(top.ev, 2),
        "raw_estimated_ev": round(top.raw_ev, 2) if top.raw_ev is not None else round(top.ev, 2),
        "reason": top.reason,
        "learning": asdict(learning_profile) if learning_profile else None,
        "top_candidates": [
            {
                "action": candidate.action.action_type.value,
                "amount": candidate.action.amount,
                "estimated_ev": round(candidate.ev, 2),
            }
            for candidate in decision.candidates[:3]
        ],
    }
    response = DecisionResponse(
        action=chosen_action.action_type.value,
        amount=chosen_action.amount,
        message=message,
        reasoning=reasoning,
    )
    append_call_log(call_log_path, live_table_json, response)
    return response


def assert_legal_response(action: Action, stack: int) -> None:
    if action.amount < 0:
        raise ValueError("Action amount cannot be negative")
    if action.amount > stack:
        raise ValueError("Action amount cannot exceed available stack")
    if action.action_type in {ActionType.FOLD, ActionType.CHECK} and action.amount != 0:
        raise ValueError(f"{action.action_type.value} must have amount 0")


def apply_learning_guard(action: Action, candidates: list, learning_profile: object | None) -> Action:
    if learning_profile is None or action.action_type != ActionType.ALL_IN:
        return action
    caution = getattr(learning_profile, "shove_caution_multiplier", 1.0)
    if caution <= 1.0:
        return action
    for candidate in candidates:
        if candidate.action.action_type != ActionType.ALL_IN:
            return candidate.action
    return action


def append_call_log(path: str | Path, live_table_json: dict, response: DecisionResponse) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "called_at": datetime.now(UTC).isoformat(),
        "source": str(live_table_json.get("source", "unknown")),
        "hand_id": live_table_json.get("hand_id"),
        "table_id": live_table_json.get("table_id"),
        "response": asdict(response),
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def decide_action_dict(live_table_json: dict, **kwargs: object) -> dict:
    return asdict(decide_action(live_table_json, **kwargs))
