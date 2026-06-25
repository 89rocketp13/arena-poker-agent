from __future__ import annotations

from dataclasses import dataclass

from .cards import Card


@dataclass(frozen=True)
class BoardTexture:
    dry: bool
    semi_wet: bool
    wet: bool
    paired: bool
    monotone: bool
    flush_draw: bool
    straight_draw: bool
    connected: bool
    nut_advantage: str
    range_advantage: str


def classify_board(board: list[Card], preflop_aggressor: str = "unknown") -> BoardTexture:
    if len(board) < 3:
        return BoardTexture(False, False, False, False, False, False, False, False, "unknown", "unknown")

    values = sorted({card.value for card in board})
    suits = [card.suit for card in board]
    suit_counts = {suit: suits.count(suit) for suit in set(suits)}
    paired = len({card.value for card in board}) < len(board)
    monotone = any(count >= 3 for count in suit_counts.values())
    flush_draw = any(count == 2 for count in suit_counts.values()) and len(board) in {3, 4}

    gaps = [b - a for a, b in zip(values, values[1:])]
    connected = len(values) >= 3 and max(gaps or [99]) <= 2
    wheel_values = set(values)
    if 14 in wheel_values:
        wheel_values.add(1)
    straight_draw = connected or any(len(wheel_values.intersection(range(start, start + 5))) >= 4 for start in range(1, 11))

    wet_score = sum([monotone, monotone, flush_draw, straight_draw, connected, paired])
    wet = wet_score >= 3
    semi_wet = wet_score == 2
    dry = wet_score <= 1

    high_card_board = max(values) >= 12
    if high_card_board and not connected:
        nut_advantage = "preflop_aggressor"
    elif connected or monotone:
        nut_advantage = "caller"
    else:
        nut_advantage = "neutral"

    range_advantage = preflop_aggressor if preflop_aggressor != "unknown" and dry else "neutral"
    return BoardTexture(dry, semi_wet, wet, paired, monotone, flush_draw, straight_draw, connected, nut_advantage, range_advantage)
