from __future__ import annotations

from .cards import Card
from .monte_carlo import EquityResult, estimate_heads_up_equity


def estimate_equity(
    hero_cards: list[Card],
    board: list[Card] | None = None,
    simulations: int = 5000,
    seed: int | None = None,
) -> EquityResult:
    return estimate_heads_up_equity(hero_cards=hero_cards, board=board, simulations=simulations, seed=seed)

