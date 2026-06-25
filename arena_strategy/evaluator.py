from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from .cards import Card

HAND_CLASS_NAMES = {
    8: "straight_flush",
    7: "four_of_a_kind",
    6: "full_house",
    5: "flush",
    4: "straight",
    3: "three_of_a_kind",
    2: "two_pair",
    1: "one_pair",
    0: "high_card",
}


@dataclass(frozen=True, order=True)
class HandRank:
    category: int
    tiebreakers: tuple[int, ...]

    @property
    def name(self) -> str:
        return HAND_CLASS_NAMES[self.category]


def _straight_high(values: list[int]) -> int | None:
    unique_values = sorted(set(values), reverse=True)
    if 14 in unique_values:
        unique_values.append(1)
    for window_start in range(len(unique_values) - 4):
        window = unique_values[window_start : window_start + 5]
        if window[0] - window[4] == 4 and len(window) == 5:
            return window[0]
    return None


def evaluate_five(cards: list[Card] | tuple[Card, ...]) -> HandRank:
    if len(cards) != 5:
        raise ValueError("evaluate_five requires exactly five cards")

    values = sorted((card.value for card in cards), reverse=True)
    suits = [card.suit for card in cards]
    counts = Counter(values)
    grouped = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    flush = len(set(suits)) == 1
    straight = _straight_high(values)

    if flush and straight:
        return HandRank(8, (straight,))

    if grouped[0][1] == 4:
        quad = grouped[0][0]
        kicker = max(value for value in values if value != quad)
        return HandRank(7, (quad, kicker))

    if grouped[0][1] == 3 and grouped[1][1] == 2:
        return HandRank(6, (grouped[0][0], grouped[1][0]))

    if flush:
        return HandRank(5, tuple(values))

    if straight:
        return HandRank(4, (straight,))

    if grouped[0][1] == 3:
        trips = grouped[0][0]
        kickers = tuple(value for value in values if value != trips)
        return HandRank(3, (trips, *kickers))

    pairs = [value for value, count in grouped if count == 2]
    if len(pairs) == 2:
        high_pair, low_pair = sorted(pairs, reverse=True)
        kicker = max(value for value in values if value not in pairs)
        return HandRank(2, (high_pair, low_pair, kicker))

    if len(pairs) == 1:
        pair = pairs[0]
        kickers = tuple(value for value in values if value != pair)
        return HandRank(1, (pair, *kickers))

    return HandRank(0, tuple(values))


def evaluate_best(cards: list[Card] | tuple[Card, ...]) -> HandRank:
    if not 5 <= len(cards) <= 7:
        raise ValueError("evaluate_best requires five to seven cards")
    return max(evaluate_five(list(combo)) for combo in combinations(cards, 5))


def compare_hands(hero_cards: list[Card], villain_cards: list[Card], board: list[Card]) -> int:
    hero_rank = evaluate_best([*hero_cards, *board])
    villain_rank = evaluate_best([*villain_cards, *board])
    if hero_rank > villain_rank:
        return 1
    if hero_rank < villain_rank:
        return -1
    return 0

