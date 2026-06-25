from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class PopulationProfile:
    hands: int
    player_entries: int
    average_players_per_hand: float
    action_counts: dict[str, int]
    fold_rate: float
    call_rate: float
    aggressive_action_rate: float
    showdown_observed_rate: float
    average_absolute_winnings: float
    recommended_exploit_rules: dict[str, Any]


def load_normalized_records(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    file_path = Path(path)
    if not file_path.exists():
        return records
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if "error" not in record:
            records.append(record)
    return records


def build_population_profile(normalized_path: str | Path = "arena_data/derived/phh_normalized.jsonl") -> PopulationProfile:
    records = load_normalized_records(normalized_path)
    action_counts: Counter[str] = Counter()
    player_counts: list[int] = []
    abs_winnings: list[float] = []
    showdown_count = 0

    for record in records:
        action_counts.update(record.get("action_summary", {}))
        players = record.get("players") or []
        player_counts.append(len(players))
        winnings = record.get("winnings") or []
        abs_winnings.extend(abs(float(value)) for value in winnings)
        if winnings or action_counts.get("showdown", 0):
            showdown_count += 1

    total_actions = sum(action_counts.values()) or 1
    fold_rate = action_counts.get("fold", 0) / total_actions
    call_rate = action_counts.get("call", 0) / total_actions
    aggressive_rate = (action_counts.get("bet", 0) + action_counts.get("raise", 0)) / total_actions
    showdown_rate = 0.0 if not records else showdown_count / len(records)
    rules = recommend_exploit_rules(fold_rate, call_rate, aggressive_rate, showdown_rate)
    return PopulationProfile(
        hands=len(records),
        player_entries=sum(player_counts),
        average_players_per_hand=round(mean(player_counts), 4) if player_counts else 0.0,
        action_counts=dict(action_counts),
        fold_rate=round(fold_rate, 4),
        call_rate=round(call_rate, 4),
        aggressive_action_rate=round(aggressive_rate, 4),
        showdown_observed_rate=round(showdown_rate, 4),
        average_absolute_winnings=round(mean(abs_winnings), 4) if abs_winnings else 0.0,
        recommended_exploit_rules=rules,
    )


def recommend_exploit_rules(fold_rate: float, call_rate: float, aggressive_rate: float, showdown_rate: float) -> dict[str, Any]:
    bluff_multiplier = 1.0
    thin_value_multiplier = 1.0
    caution_notes: list[str] = []
    if fold_rate >= 0.33:
        bluff_multiplier += 0.15
        caution_notes.append("Population appears fold-heavy; pressure lines may overperform.")
    if call_rate >= 0.30 or showdown_rate >= 0.45:
        bluff_multiplier -= 0.20
        thin_value_multiplier += 0.20
        caution_notes.append("Population appears sticky; reduce low-equity bluffs and value bet thinner.")
    if aggressive_rate >= 0.28:
        bluff_multiplier -= 0.10
        caution_notes.append("Population aggression is high; protect calling ranges and avoid marginal bluff-catches.")
    return {
        "bluff_frequency_multiplier": round(max(bluff_multiplier, 0.45), 3),
        "thin_value_frequency_multiplier": round(thin_value_multiplier, 3),
        "notes": caution_notes or ["No strong population exploit detected yet."],
    }


def write_population_profile(
    normalized_path: str | Path = "arena_data/derived/phh_normalized.jsonl",
    profile_path: str | Path = "arena_data/derived/population_profile.json",
) -> dict[str, Any]:
    profile = build_population_profile(normalized_path)
    output = Path(profile_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(profile), indent=2, sort_keys=True), encoding="utf-8")
    return asdict(profile)


if __name__ == "__main__":
    print(json.dumps(write_population_profile(), indent=2, sort_keys=True))

