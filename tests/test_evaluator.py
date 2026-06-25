from arena_strategy.cards import parse_cards
from arena_strategy.evaluator import evaluate_best


def test_evaluates_royal_flush_over_trips() -> None:
    cards = parse_cards("Ah Kh Qh Jh Th As Ad")
    assert evaluate_best(cards).name == "straight_flush"


def test_wheel_straight() -> None:
    cards = parse_cards("Ah 2d 3c 4s 5h Kd Qc")
    rank = evaluate_best(cards)
    assert rank.name == "straight"
    assert rank.tiebreakers == (5,)

