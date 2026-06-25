from arena_strategy.board_texture import classify_board
from arena_strategy.cards import parse_cards
from arena_strategy.decision_engine import DecisionEngine
from arena_strategy.icm import icm_equities
from arena_strategy.opponent_model import OpponentProfile
from arena_strategy.ranges import RangeManager
from arena_strategy.state_parser import parse_table_state


def test_board_texture_detects_wet_board() -> None:
    texture = classify_board(parse_cards("Jh Th 9h"))
    assert texture.wet
    assert texture.monotone
    assert texture.straight_draw


def test_range_manager_loads_fixture() -> None:
    manager = RangeManager.from_json("arena_data/preflop/sample_ranges.json")
    assert manager.contains("utg_open", "AA")
    assert not manager.contains("utg_open", "72o")


def test_opponent_profile_classifies_calling_station_tendency() -> None:
    profile = OpponentProfile("villain")
    for _ in range(60):
        profile.update_hand(vpip=True, pfr=False, folded_to_cbet=False, saw_showdown=True)
    assert profile.label in {"calling_station", "loose_passive"}


def test_icm_equities_sum_to_payouts() -> None:
    equities = icm_equities([50, 30, 20], [50.0, 30.0, 20.0])
    assert round(sum(equities), 6) == 100.0
    assert equities[0] > equities[1] > equities[2]


def test_decision_engine_returns_legal_action_and_context() -> None:
    state = parse_table_state(
        {
            "hero_cards": ["Ah", "Kh"],
            "board": ["Qh", "Jh", "2c"],
            "pot": 1200,
            "to_call": 300,
            "hero_stack": 9000,
            "min_raise": 600,
            "big_blind": 200,
            "position": "button",
            "opponents_in_hand": 1,
            "preflop_aggressor": "hero",
        }
    )
    decision = DecisionEngine(simulations=200, seed=3).decide(state)
    assert decision.action in decision.context.legal_actions
    assert 0.0 <= decision.context.equity <= 1.0
    assert decision.candidates

