from arena_strategy.betting import ActionType
from arena_strategy.cards import parse_cards
from arena_strategy.decision_engine import DecisionEngine
from arena_strategy.preflop import recommend_preflop
from arena_strategy.state_parser import TableState


def make_state(hero_cards, position="button", to_call=0, stack=10000):
    return TableState(
        hero_cards=parse_cards(hero_cards),
        board=[],
        pot=300,
        to_call=to_call,
        hero_stack=stack,
        min_raise=400,
        big_blind=200,
        position=position,
        opponents_in_hand=1,
    )


def test_premium_button_opens_with_chart_gate() -> None:
    state = make_state("Ah Kh", "button")
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type == ActionType.BET


def test_trash_early_position_does_not_open() -> None:
    state = make_state("7c 2d", "utg")
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type == ActionType.CHECK


def test_facing_raise_folds_trash() -> None:
    state = make_state("7c 2d", "button", to_call=600)
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type == ActionType.FOLD


def test_decision_engine_uses_preflop_gate_instead_of_shoving() -> None:
    state = make_state("Ah Kh", "button")
    decision = DecisionEngine(simulations=20, seed=1).decide(state)
    assert decision.action.action_type == ActionType.BET
    assert "Preflop chart gate" in decision.candidates[0].reason

