from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .cards import Card, canonical_hand


@dataclass(frozen=True)
class RangeEntry:
    hand: str
    frequency: float


class RangeManager:
    def __init__(self, ranges: dict[str, dict[str, float]] | None = None) -> None:
        self._ranges = ranges or {}

    @classmethod
    def from_json(cls, path: str | Path) -> "RangeManager":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        ranges = {name: {hand: float(freq) for hand, freq in hands.items()} for name, hands in data.items()}
        return cls(ranges)

    def frequency(self, range_name: str, hand: str | tuple[Card, Card]) -> float:
        key = canonical_hand(*hand) if isinstance(hand, tuple) else hand
        return self._ranges.get(range_name, {}).get(key, 0.0)

    def contains(self, range_name: str, hand: str | tuple[Card, Card], threshold: float = 0.5) -> bool:
        return self.frequency(range_name, hand) >= threshold

    def hands(self, range_name: str) -> list[RangeEntry]:
        return [RangeEntry(hand, freq) for hand, freq in sorted(self._ranges.get(range_name, {}).items())]

