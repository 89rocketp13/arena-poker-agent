from __future__ import annotations

from collections import Counter
from pathlib import Path

from .recorder import HandRecord, iter_records


def generate_leak_report(
    records_path: str | Path = "arena-data/hand-records.jsonl",
    report_path: str | Path = "arena_strategy/reports/latest-leak-report.md",
) -> str:
    records = iter_records(records_path)
    report = build_report(records)
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return report


def build_report(records: list[HandRecord]) -> str:
    action_counts: Counter[str] = Counter()
    tags: Counter[str] = Counter()
    illegal_or_missing = 0
    total_profit = 0.0
    result_count = 0

    for record in records:
        if record.chosen_action:
            action_counts[str(record.chosen_action.get("action", "unknown"))] += 1
        else:
            illegal_or_missing += 1
        tags.update(record.tags)
        if record.final_result and "chip_delta" in record.final_result:
            total_profit += float(record.final_result["chip_delta"])
            result_count += 1

    average_profit = total_profit / result_count if result_count else 0.0
    lines = [
        "# Arena Poker Leak Report",
        "",
        f"Hands reviewed: {len(records)}",
        f"Hands with results: {result_count}",
        f"Average chip delta: {average_profit:.2f}",
        f"Missing chosen action: {illegal_or_missing}",
        "",
        "## Action Mix",
        "",
    ]
    if action_counts:
        for action, count in action_counts.most_common():
            lines.append(f"- {action}: {count}")
    else:
        lines.append("- No actions recorded yet.")

    lines.extend(["", "## Tags", ""])
    if tags:
        for tag, count in tags.most_common():
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("- No tags recorded yet.")

    lines.extend(
        [
            "",
            "## Next Review Questions",
            "",
            "- Are all returned actions legal under Arena's available-actions payload?",
            "- Is the action mix too shove-heavy for the current stack depth?",
            "- Are river bluffs losing against calling-station profiles?",
            "- Are bubble and final-table spots using ICM pressure?",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(generate_leak_report())

