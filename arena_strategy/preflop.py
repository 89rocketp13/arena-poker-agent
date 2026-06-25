from __future__ import annotations

from dataclasses import dataclass

from .betting import Action, ActionType
from .cards import Card, canonical_hand
from .state_parser import TableState


EARLY_OPEN = {
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "KQs",
    "AKo", "AQo",
}
MIDDLE_OPEN = EARLY_OPEN | {
    "88", "77", "ATs", "KJs", "QJs", "JTs", "T9s", "AJo", "KQo",
}
LATE_OPEN = MIDDLE_OPEN | {
    "66", "55", "44", "33", "22",
    "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KTs", "QTs", "J9s", "98s", "87s", "76s", "65s",
    "ATo", "KJo", "QJo",
}
BLIND_DEFEND = LATE_OPEN | {
    "K9s", "Q9s", "J8s", "T8s", "97s", "86s", "75s", "64s",
    "A9o", "A8o", "KTo", "QTo", "JTo",
}

THREE_BET_VALUE = {"AA", "KK", "QQ", "JJ", "AKs", "AKo"}
THREE_BET_MIXED = {"TT", "99", "AQs", "AJs", "KQs", "AQo", "A5s", "A4s"}
CALL_VS_RAISE = {
    "QQ", "JJ", "TT", "99", "88", "77",
    "AQs", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "T9s", "98s",
    "AQo", "AJo", "KQo",
}

PUSH_10BB = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s", "A4s", "KQs",
    "AKo", "AQo", "AJo", "KQo",
}
PUSH_15BB = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88",
    "AKs", "AQs", "AJs", "ATs", "A5s", "A4s", "KQs",
    "AKo", "AQo", "AJo",
}

EARLY_POSITIONS = {"utg", "utg1", "utg+1", "lj", "lojack", "early"}
MIDDLE_POSITIONS = {"hj", "hijack", "mp", "middle"}
LATE_POSITIONS = {"co", "cutoff", "btn", "button", "late"}
BLIND_POSITIONS = {"sb", "small_blind", "bb", "big_blind"}


@dataclass(frozen=True)
class PreflopRecommendation:
    action: Action
    hand_class: str
    chart: str
    confidence: str
    reason: str


def recommend_preflop(state: TableState) -> PreflopRecommendation | None:
    if state.board:
        return None
    hand = canonical_hand(state.hero_cards[0], state.hero_cards[1])
    bb_stack = state.hero_stack / state.big_blind if state.big_blind else 999.0

    if bb_stack <= 10:
        return _short_stack(hand, state, PUSH_10BB, "push_fold_10bb")
    if bb_stack <= 15:
        return _short_stack(hand, state, PUSH_15BB, "push_fold_15bb")

    if state.to_call > 0:
        return _facing_raise(hand, state)
    return _open_decision(hand, state)


def _short_stack(hand: str, state: TableState, push_range: set[str], chart: str) -> PreflopRecommendation:
    if hand in push_range:
        return PreflopRecommendation(
            Action(ActionType.ALL_IN, state.hero_stack),
            hand,
            chart,
            "medium",
            f"{hand} is in the {chart} shove range at this stack depth.",
        )
    if state.to_call == 0:
        return PreflopRecommendation(Action(ActionType.CHECK), hand, chart, "medium", f"{hand} is not in the {chart} shove range.")
    return PreflopRecommendation(Action(ActionType.FOLD), hand, chart, "medium", f"{hand} is not strong enough to continue at this stack depth.")


def _facing_raise(hand: str, state: TableState) -> PreflopRecommendation:
    if hand in THREE_BET_VALUE:
        amount = min(state.hero_stack, max(state.to_call + state.min_raise, state.to_call * 3))
        return PreflopRecommendation(Action(ActionType.RAISE, amount), hand, "three_bet_value", "medium", f"{hand} is a value 3-bet hand.")
    if hand in THREE_BET_MIXED and state.hero_stack / max(state.pot, 1) <= 8:
        amount = min(state.hero_stack, max(state.to_call + state.min_raise, state.to_call * 3))
        return PreflopRecommendation(Action(ActionType.RAISE, amount), hand, "three_bet_mixed", "low", f"{hand} is a mixed 3-bet candidate; use caution without villain reads.")
    if hand in CALL_VS_RAISE or (_is_blind(state.position) and hand in BLIND_DEFEND):
        return PreflopRecommendation(Action(ActionType.CALL, min(state.to_call, state.hero_stack)), hand, "call_vs_raise", "medium", f"{hand} can continue versus this price.")
    return PreflopRecommendation(Action(ActionType.FOLD), hand, "fold_vs_raise", "medium", f"{hand} is outside the continue range versus a raise.")


def _open_decision(hand: str, state: TableState) -> PreflopRecommendation:
    position = state.position.lower()
    if _is_early(position):
        chart, opening_range = "early_open", EARLY_OPEN
    elif _is_middle(position):
        chart, opening_range = "middle_open", MIDDLE_OPEN
    elif _is_late(position) or _is_blind(position):
        chart, opening_range = "late_open", LATE_OPEN
    else:
        chart, opening_range = "unknown_position_tight_open", EARLY_OPEN

    if hand in opening_range:
        amount = min(state.hero_stack, max(state.big_blind * 2, state.min_raise))
        return PreflopRecommendation(Action(ActionType.BET, amount), hand, chart, "medium", f"{hand} is in the {chart} range.")
    return PreflopRecommendation(Action(ActionType.CHECK), hand, chart, "medium", f"{hand} is outside the {chart} range; do not open voluntarily.")


def _is_early(position: str) -> bool:
    return position in EARLY_POSITIONS


def _is_middle(position: str) -> bool:
    return position in MIDDLE_POSITIONS


def _is_late(position: str) -> bool:
    return position in LATE_POSITIONS


def _is_blind(position: str) -> bool:
    return position in BLIND_POSITIONS

