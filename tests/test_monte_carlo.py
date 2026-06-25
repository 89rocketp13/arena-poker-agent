from arena_strategy.cards import parse_cards
from arena_strategy.monte_carlo import estimate_heads_up_equity


def test_known_aces_dominate_kings_preflop() -> None:
    result = estimate_heads_up_equity(
        hero_cards=parse_cards("As Ah"),
        villain_cards=parse_cards("Kd Kc"),
        simulations=500,
        seed=11,
    )
    assert result.equity > 0.75

