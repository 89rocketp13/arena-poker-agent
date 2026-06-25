from __future__ import annotations

import random
from dataclasses import dataclass

from .cards import Card, full_deck
from .evaluator import compare_hands


@dataclass(frozen=True)
class EquityResult:
    wins: int
    losses: int
    ties: int
    simulations: int

    @property
    def equity(self) -> float:
        if self.simulations == 0:
            return 0.0
        return (self.wins + self.ties * 0.5) / self.simulations


def estimate_heads_up_equity(
    hero_cards: list[Card],
    board: list[Card] | None = None,
    villain_cards: list[Card] | None = None,
    simulations: int = 5000,
    seed: int | None = None,
) -> EquityResult:
    if len(hero_cards) != 2:
        raise ValueError("Hero must have exactly two hole cards")
    board = board or []
    villain_cards = villain_cards or []
    if len(board) > 5:
        raise ValueError("Board cannot contain more than five cards")
    if villain_cards and len(villain_cards) != 2:
        raise ValueError("Villain must have zero or two known hole cards")

    rng = random.Random(seed)
    known = [*hero_cards, *board, *villain_cards]
    if len(set(known)) != len(known):
        raise ValueError("Duplicate cards are not allowed")
    deck = full_deck(known)

    wins = losses = ties = 0
    missing_board = 5 - len(board)
    missing_villain = 0 if villain_cards else 2
    draw_count = missing_board + missing_villain

    for _ in range(simulations):
        sample = rng.sample(deck, draw_count)
        sampled_villain = villain_cards or sample[:2]
        sampled_board = [*board, *sample[missing_villain:]]
        result = compare_hands(hero_cards, sampled_villain, sampled_board)
        if result > 0:
            wins += 1
        elif result < 0:
            losses += 1
        else:
            ties += 1
    return EquityResult(wins=wins, losses=losses, ties=ties, simulations=simulations)

