from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HandRecord:
    hand_id: str
    table_id: str
    observed_at: str
    live_state: dict[str, Any]
    legal_actions: list[dict[str, Any]]
    chosen_action: dict[str, Any] | None = None
    hero_reasoning: str | None = None
    final_result: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)


class HandRecorder:
    def __init__(self, path: str | Path = "arena-data/hand-records.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: HandRecord) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def record_from_recent_table(
        self,
        hand_id: str,
        table_id: str,
        live_state: dict[str, Any],
        legal_actions: list[dict[str, Any]],
        chosen_action: dict[str, Any] | None = None,
        hero_reasoning: str | None = None,
        final_result: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> HandRecord:
        record = HandRecord(
            hand_id=hand_id,
            table_id=table_id,
            observed_at=datetime.now(UTC).isoformat(),
            live_state=live_state,
            legal_actions=legal_actions,
            chosen_action=chosen_action,
            hero_reasoning=hero_reasoning,
            final_result=final_result,
            tags=tags or [],
        )
        self.append(record)
        return record


def iter_records(path: str | Path = "arena-data/hand-records.jsonl") -> list[HandRecord]:
    records: list[HandRecord] = []
    file_path = Path(path)
    if not file_path.exists():
        return records
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(HandRecord(**json.loads(line)))
    return records

