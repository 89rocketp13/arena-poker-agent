from __future__ import annotations

import json
import re
import tomllib
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


REQUIRED_PHH_FIELDS = {
    "variant",
    "antes",
    "blinds_or_straddles",
    "bring_in",
    "small_bet",
    "big_bet",
    "min_bet",
    "starting_stacks",
    "actions",
}


@dataclass(frozen=True)
class NormalizedPHHHand:
    source_format: str
    source_file: str
    hand_id: str
    variant: str
    players: list[str]
    table: str | int | None
    hand: str | int | None
    blinds_or_straddles: list[int | float]
    antes: list[int | float]
    starting_stacks: list[int | float | None]
    finishing_stacks: list[int | float] | None
    winnings: list[int | float] | None
    actions: list[str]
    action_summary: dict[str, int]
    raw_metadata: dict[str, Any] = field(default_factory=dict)


def load_phh(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("rb") as handle:
        data = tomllib.load(handle)
    missing = sorted(REQUIRED_PHH_FIELDS.difference(data))
    if missing:
        raise ValueError(f"{file_path} is missing required PHH fields: {', '.join(missing)}")
    if not isinstance(data["actions"], list):
        raise ValueError(f"{file_path} PHH actions must be an array")
    return data


def normalize_phh(path: str | Path, dataset_root: str | Path | None = None) -> NormalizedPHHHand:
    file_path = Path(path)
    data = load_phh(file_path)
    root = Path(dataset_root) if dataset_root else file_path.parent
    source_file = str(file_path.relative_to(root)) if file_path.is_relative_to(root) else str(file_path)
    action_summary = dict(Counter(classify_action(action) for action in data["actions"]))
    players = [str(player) for player in data.get("players", [])]
    hand_id = str(data.get("hand", file_path.stem))
    raw_metadata = {
        key: value
        for key, value in data.items()
        if key not in {
            "variant",
            "players",
            "table",
            "hand",
            "blinds_or_straddles",
            "antes",
            "starting_stacks",
            "finishing_stacks",
            "winnings",
            "actions",
        }
    }
    return NormalizedPHHHand(
        source_format="phh",
        source_file=source_file,
        hand_id=hand_id,
        variant=str(data["variant"]),
        players=players,
        table=data.get("table"),
        hand=data.get("hand"),
        blinds_or_straddles=list(data["blinds_or_straddles"]),
        antes=list(data["antes"]),
        starting_stacks=list(data["starting_stacks"]),
        finishing_stacks=list(data["finishing_stacks"]) if "finishing_stacks" in data else None,
        winnings=list(data["winnings"]) if "winnings" in data else None,
        actions=[str(action) for action in data["actions"]],
        action_summary=action_summary,
        raw_metadata=raw_metadata,
    )


def iter_phh_files(input_path: str | Path) -> Iterable[Path]:
    path = Path(input_path)
    if path.is_file():
        yield path
        return
    for pattern in ("*.phh", "*.toml"):
        yield from sorted(path.rglob(pattern))


def import_phh_dataset(
    input_path: str | Path,
    output_path: str | Path = "arena_data/derived/phh_normalized.jsonl",
    limit: int | None = None,
) -> dict[str, int]:
    files_seen = records_written = errors = 0
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    root = Path(input_path)
    with output.open("w", encoding="utf-8") as handle:
        for file_path in iter_phh_files(root):
            if limit is not None and records_written >= limit:
                break
            files_seen += 1
            try:
                hand = normalize_phh(file_path, root if root.is_dir() else root.parent)
                handle.write(json.dumps(asdict(hand), sort_keys=True) + "\n")
                records_written += 1
            except Exception as exc:
                errors += 1
                handle.write(json.dumps({"source_file": str(file_path), "error": str(exc)}, sort_keys=True) + "\n")
    return {"files_seen": files_seen, "records_written": records_written, "errors": errors}


def classify_action(action: str) -> str:
    text = action.lower().strip()
    tokens = re.split(r"[\s:(),]+", text)
    token_set = set(token for token in tokens if token)
    if {"fold", "f"} & token_set or text.endswith(" f"):
        return "fold"
    if {"check", "x"} & token_set:
        return "check"
    if {"call", "c"} & token_set:
        return "call"
    if {"raise", "r"} & token_set:
        return "raise"
    if {"bet", "b"} & token_set:
        return "bet"
    if {"ante", "blind", "straddle", "bring-in"} & token_set:
        return "forced_bet"
    if text.startswith("d") or "deal" in token_set:
        return "deal"
    if "show" in token_set or "muck" in token_set:
        return "showdown"
    return "other"

