from arena_strategy.analyze import generate_leak_report
from arena_strategy.decision import decide_action_dict
from arena_strategy.learning import LearningStore
from arena_strategy.recorder import HandRecorder, iter_records


def test_decision_facade_returns_legal_shaped_response() -> None:
    payload = {
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
    response = decide_action_dict(payload, simulations=50, seed=9, use_learning=False)
    assert response["action"] in {"fold", "check", "call", "bet", "raise", "all_in"}
    assert 0 <= response["amount"] <= payload["hero_stack"]
    assert response["message"]
    assert "equity" in response["reasoning"]
    if response["action"] in {"fold", "check"}:
        assert response["amount"] == 0


def test_decision_facade_writes_call_log(tmp_path) -> None:
    payload = {
        "source": "test-hermes",
        "hand_id": "hand-call-log",
        "table_id": "table-call-log",
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
    call_log = tmp_path / "decision-calls.jsonl"
    decide_action_dict(payload, simulations=30, seed=2, use_learning=False, call_log_path=call_log)
    text = call_log.read_text(encoding="utf-8")
    assert "test-hermes" in text
    assert "hand-call-log" in text


def test_recorder_writes_jsonl_and_analyzer_reports(tmp_path) -> None:
    records_path = tmp_path / "hand-records.jsonl"
    report_path = tmp_path / "report.md"
    recorder = HandRecorder(records_path)
    recorder.record_from_recent_table(
        hand_id="hand-1",
        table_id="table-1",
        live_state={"pot": 100},
        legal_actions=[{"action": "fold"}, {"action": "call", "amount": 20}],
        chosen_action={"action": "call", "amount": 20},
        hero_reasoning="Pot odds call.",
        final_result={"chip_delta": 40},
        tags=["pot-odds", "showdown"],
    )

    records = iter_records(records_path)
    assert len(records) == 1
    assert records[0].hand_id == "hand-1"

    report = generate_leak_report(records_path, report_path)
    assert "Hands reviewed: 1" in report
    assert "Average chip delta: 40.00" in report
    assert report_path.exists()


def test_learning_store_rebuilds_profile_and_flags_bad_shoves(tmp_path) -> None:
    records_path = tmp_path / "hand-records.jsonl"
    profile_path = tmp_path / "learning-profile.json"
    recorder = HandRecorder(records_path)
    for index in range(6):
        recorder.record_from_recent_table(
            hand_id=f"hand-{index}",
            table_id="table-1",
            live_state={"pot": 100},
            legal_actions=[{"action": "fold"}, {"action": "all_in", "amount": 1000}],
            chosen_action={"action": "all_in", "amount": 1000},
            final_result={"chip_delta": -100},
            tags=["all-in-loss"],
        )

    profile = LearningStore(records_path, profile_path).rebuild_from_records()
    assert profile.hands_seen == 6
    assert profile.shove_caution_multiplier > 1.0
    assert profile_path.exists()
