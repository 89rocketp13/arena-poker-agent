from __future__ import annotations

from dataclasses import dataclass

from .betting import BettingState
from .cards import Card, parse_cards


@dataclass(frozen=True)
class TableState:
    hero_cards: list[Card]
    board: list[Card]
    pot: int
    to_call: int
    hero_stack: int
    min_raise: int
    big_blind: int
    position: str
    opponents_in_hand: int
    preflop_aggressor: str = "unknown"

    @property
    def betting_state(self) -> BettingState:
        return BettingState(
            pot=self.pot,
            to_call=self.to_call,
            stack=self.hero_stack,
            min_raise=self.min_raise,
            big_blind=self.big_blind,
        )


def parse_table_state(payload: dict) -> TableState:
    return TableState(
        hero_cards=parse_cards(payload["hero_cards"]),
        board=parse_cards(payload.get("board", [])),
        pot=int(payload["pot"]),
        to_call=int(payload.get("to_call", 0)),
        hero_stack=int(payload["hero_stack"]),
        min_raise=int(payload.get("min_raise", payload.get("big_blind", 0))),
        big_blind=int(payload["big_blind"]),
        position=str(payload.get("position", "unknown")),
        opponents_in_hand=int(payload.get("opponents_in_hand", 1)),
        preflop_aggressor=str(payload.get("preflop_aggressor", "unknown")),
    )

