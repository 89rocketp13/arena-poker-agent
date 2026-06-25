from pathlib import Path

from arena_strategy.phh_ingest import classify_action, import_phh_dataset, normalize_phh
from arena_strategy.population import build_population_profile, write_population_profile


def write_sample_phh(path: Path) -> None:
    path.write_text(
        """
variant = "NT"
antes = [0, 0]
blinds_or_straddles = [50, 100]
bring_in = 0
small_bet = 0
big_bet = 0
min_bet = 100
starting_stacks = [10000, 10000]
players = ["alice", "bob"]
hand = "sample-1"
table = "table-1"
actions = [
  "p1 raise 300",
  "p2 call 300",
  "deal flop Ah Kh 2c",
  "p1 bet 400",
  "p2 fold"
]
finishing_stacks = [10400, 9600]
winnings = [400, -400]
""".strip(),
        encoding="utf-8",
    )


def test_classify_action_handles_common_words() -> None:
    assert classify_action("p1 raise 300") == "raise"
    assert classify_action("p2 call 300") == "call"
    assert classify_action("p2 fold") == "fold"
    assert classify_action("deal flop Ah Kh 2c") == "deal"


def test_normalize_phh_fixture(tmp_path) -> None:
    phh_path = tmp_path / "sample.phh"
    write_sample_phh(phh_path)
    hand = normalize_phh(phh_path, tmp_path)
    assert hand.source_format == "phh"
    assert hand.hand_id == "sample-1"
    assert hand.action_summary["raise"] == 1
    assert hand.action_summary["fold"] == 1


def test_import_phh_dataset_and_population_profile(tmp_path) -> None:
    input_dir = tmp_path / "phh"
    input_dir.mkdir()
    write_sample_phh(input_dir / "sample.phh")
    output = tmp_path / "normalized.jsonl"
    profile_path = tmp_path / "profile.json"

    summary = import_phh_dataset(input_dir, output)
    assert summary == {"files_seen": 1, "records_written": 1, "errors": 0}

    profile = build_population_profile(output)
    assert profile.hands == 1
    assert profile.action_counts["raise"] == 1

    written = write_population_profile(output, profile_path)
    assert written["hands"] == 1
    assert profile_path.exists()

