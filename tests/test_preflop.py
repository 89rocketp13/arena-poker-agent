from arena_strategy.betting import ActionType
from arena_strategy.cards import parse_cards
from arena_strategy.decision import decide_action_dict
from arena_strategy.decision_engine import DecisionEngine
from arena_strategy.preflop import estimate_preflop_win_chance, recommend_preflop
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


def test_trash_early_position_applies_small_pressure_when_free() -> None:
    state = make_state("7c 2d", "utg")
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type == ActionType.BET
    assert recommendation.action.amount == state.min_raise + 3


def test_facing_raise_folds_trash() -> None:
    state = make_state("7c 2d", "button", to_call=600)
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type == ActionType.FOLD


def test_tiny_button_price_with_k9o_never_folds() -> None:
    state = TableState(
        hero_cards=parse_cards("Ks 9h"),
        board=[],
        pot=3,
        to_call=1,
        hero_stack=986,
        min_raise=4,
        big_blind=2,
        position="button",
        opponents_in_hand=1,
    )
    recommendation = recommend_preflop(state)
    assert recommendation is not None
    assert recommendation.action.action_type in {ActionType.CALL, ActionType.RAISE}
    assert recommendation.action.amount == 8


def test_live_facade_never_folds_tiny_preflop_price() -> None:
    response = decide_action_dict(
        {
            "source": "tiny-price-safety",
            "hand_id": "ato-tiny",
            "table_id": "test",
            "hero_cards": ["Th", "Ad"],
            "board": [],
            "pot": 3,
            "to_call": 1,
            "hero_stack": 987,
            "min_raise": 4,
            "big_blind": 2,
            "position": "button",
            "opponents_in_hand": 1,
        },
        simulations=10,
        seed=1,
        use_learning=False,
        call_log_path="arena-data/test-decision-calls.jsonl",
    )
    assert response["action"] in {"call", "raise", "bet"}
    assert response["amount"] == 8


def test_estimated_preflop_chance_crosses_25pct_for_ato() -> None:
    assert estimate_preflop_win_chance(parse_cards("Th Ad")) >= 0.25


def test_decision_engine_uses_preflop_gate_instead_of_shoving() -> None:
    state = make_state("Ah Kh", "button")
    decision = DecisionEngine(simulations=20, seed=1).decide(state)
    assert decision.action.action_type == ActionType.BET
    assert "Preflop chart gate" in decision.candidates[0].reason
