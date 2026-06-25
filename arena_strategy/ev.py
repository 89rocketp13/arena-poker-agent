from __future__ import annotations

from .betting import Action, ActionType


def pot_odds(to_call: int, pot: int) -> float:
    if to_call <= 0:
        return 0.0
    return to_call / (pot + to_call)


def call_ev(equity: float, pot: int, to_call: int) -> float:
    return equity * (pot + to_call) - (1.0 - equity) * to_call


def fold_equity_break_even(risk: int, reward: int) -> float:
    if risk + reward <= 0:
        return 1.0
    return risk / (risk + reward)


def simple_action_ev(action: Action, equity: float, pot: int, to_call: int, fold_equity: float = 0.0) -> float:
    if action.action_type == ActionType.FOLD:
        return 0.0
    if action.action_type == ActionType.CHECK:
        return equity * pot
    if action.action_type == ActionType.CALL:
        return call_ev(equity, pot, to_call)
    if action.action_type in {ActionType.BET, ActionType.RAISE, ActionType.ALL_IN}:
        risk = max(action.amount, 0)
        showdown_ev = equity * (pot + risk) - (1.0 - equity) * risk
        return fold_equity * pot + (1.0 - fold_equity) * showdown_ev
    raise ValueError(f"Unsupported action type: {action.action_type}")

