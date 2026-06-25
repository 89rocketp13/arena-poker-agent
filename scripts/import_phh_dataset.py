from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arena_strategy.phh_ingest import import_phh_dataset
from arena_strategy.population import write_population_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Import University of Toronto CPRG PHH files into normalized JSONL.")
    parser.add_argument("--input", required=True, help="PHH file or directory containing .phh/.toml files.")
    parser.add_argument("--output", default="arena_data/derived/phh_normalized.jsonl")
    parser.add_argument("--profile", default="arena_data/derived/population_profile.json")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    summary = import_phh_dataset(args.input, args.output, args.limit)
    profile = write_population_profile(args.output, args.profile)
    print(json.dumps({"import": summary, "profile": profile}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

