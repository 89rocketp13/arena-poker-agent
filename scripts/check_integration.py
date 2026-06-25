from __future__ import annotations

import json
from pathlib import Path


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> None:
    call_log = Path("arena-data/decision-calls.jsonl")
    hand_records = Path("arena-data/hand-records.jsonl")
    learning_profile = Path("arena-data/learning-profile.json")
    skill = Path.home() / ".hermes" / "skills" / "gaming" / "arena-poker-strategy" / "SKILL.md"

    print(f"Hermes skill installed: {skill.exists()} ({skill})")
    print(f"Decision calls logged: {count_jsonl(call_log)} ({call_log})")
    print(f"Hand records logged: {count_jsonl(hand_records)} ({hand_records})")
    print(f"Learning profile exists: {learning_profile.exists()} ({learning_profile})")
    if learning_profile.exists():
        profile = json.loads(learning_profile.read_text(encoding="utf-8"))
        print(f"Hands learned from: {profile.get('hands_seen', 0)}")
        print(f"Shove caution multiplier: {profile.get('shove_caution_multiplier', 1.0)}")


if __name__ == "__main__":
    main()

