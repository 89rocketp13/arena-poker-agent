from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .recorder import iter_records


@dataclass
class LearningProfile:
    hands_seen: int = 0
    total_chip_delta: float = 0.0
    action_counts: dict[str, int] = field(default_factory=dict)
    action_chip_delta: dict[str, float] = field(default_factory=dict)
    aggression_multiplier: float = 1.0
    shove_caution_multiplier: float = 1.0

    @property
    def average_chip_delta(self) -> float:
        return 0.0 if self.hands_seen == 0 else self.total_chip_delta / self.hands_seen


class LearningStore:
    def __init__(
        self,
        records_path: str | Path = "arena-data/hand-records.jsonl",
        profile_path: str | Path = "arena-data/learning-profile.json",
    ) -> None:
        self.records_path = Path(records_path)
        self.profile_path = Path(profile_path)
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> LearningProfile:
        if not self.profile_path.exists():
            return LearningProfile()
        return LearningProfile(**json.loads(self.profile_path.read_text(encoding="utf-8")))

    def save(self, profile: LearningProfile) -> None:
        self.profile_path.write_text(json.dumps(asdict(profile), indent=2, sort_keys=True), encoding="utf-8")

    def rebuild_from_records(self) -> LearningProfile:
        profile = LearningProfile()
        for record in iter_records(self.records_path):
            if not record.chosen_action or not record.final_result or "chip_delta" not in record.final_result:
                continue
            action = str(record.chosen_action.get("action", "unknown"))
            delta = float(record.final_result["chip_delta"])
            profile.hands_seen += 1
            profile.total_chip_delta += delta
            profile.action_counts[action] = profile.action_counts.get(action, 0) + 1
            profile.action_chip_delta[action] = profile.action_chip_delta.get(action, 0.0) + delta

        all_in_count = profile.action_counts.get("all_in", 0)
        all_in_delta = profile.action_chip_delta.get("all_in", 0.0)
        if all_in_count >= 5 and all_in_delta / all_in_count < 0:
            profile.shove_caution_multiplier = 1.35
            profile.aggression_multiplier = 0.9
        elif profile.average_chip_delta > 0:
            profile.shove_caution_multiplier = 1.0
            profile.aggression_multiplier = 1.05

        self.save(profile)
        return profile


def rebuild_learning_profile(
    records_path: str | Path = "arena-data/hand-records.jsonl",
    profile_path: str | Path = "arena-data/learning-profile.json",
) -> dict:
    return asdict(LearningStore(records_path, profile_path).rebuild_from_records())


if __name__ == "__main__":
    print(json.dumps(rebuild_learning_profile(), indent=2, sort_keys=True))

