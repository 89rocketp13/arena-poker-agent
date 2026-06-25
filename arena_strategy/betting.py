from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    amount: int = 0


@dataclass(frozen=True)
class BettingState:
    pot: int
    to_call: int
    stack: int
    min_raise: int
    big_blind: int


def legal_actions(state: BettingState) -> list[Action]:
    if state.stack <= 0:
        return []

    actions: list[Action] = [Action(ActionType.FOLD)]
    if state.to_call == 0:
        actions.append(Action(ActionType.CHECK))
        min_bet = max(state.big_blind, state.min_raise)
        if state.stack >= min_bet:
            actions.append(Action(ActionType.BET, min_bet))
    else:
        call_amount = min(state.to_call, state.stack)
        actions.append(Action(ActionType.CALL, call_amount))
        min_raise_to = state.to_call + state.min_raise
        if state.stack > min_raise_to:
            actions.append(Action(ActionType.RAISE, min_raise_to))

    actions.append(Action(ActionType.ALL_IN, state.stack))
    return dedupe_actions(actions)


def dedupe_actions(actions: list[Action]) -> list[Action]:
    seen: set[tuple[ActionType, int]] = set()
    unique: list[Action] = []
    for action in actions:
        key = (action.action_type, action.amount)
        if key not in seen:
            unique.append(action)
            seen.add(key)
    return unique


def stack_to_pot_ratio(stack: int, pot: int) -> float:
    return float("inf") if pot <= 0 else stack / pot

