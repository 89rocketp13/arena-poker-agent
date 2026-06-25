# University of Toronto CPRG PHH Dataset Integration

The project now supports importing PHH files from the University of Toronto CPRG Poker Hand History ecosystem.

PHH is a TOML-based poker hand-history format. The upstream specification is maintained at:

- https://github.com/uoftcprg/phh-std
- https://phh.readthedocs.io/

The PHH paper describes the format as a concise, human-readable, machine-friendly hand-history representation. The specification lists required fields including `variant`, `antes`, `blinds_or_straddles`, `bring_in`, `small_bet`, `big_bet`, `min_bet`, `starting_stacks`, and `actions`.

## What Is Committed

Committed:

- PHH parser and normalizer
- Population tendency builder
- CLI import script
- Tests with tiny synthetic PHH fixtures

Not committed:

- Raw University of Toronto / CPRG dataset files
- Large downloaded hand-history archives
- Derived profiles generated from private/local data

Raw PHH files should be placed locally under:

```text
arena_data/external/phh/
```

That directory is gitignored except for `.gitkeep`.

## Import

```bash
python3 scripts/import_phh_dataset.py \
  --input arena_data/external/phh \
  --output arena_data/derived/phh_normalized.jsonl \
  --profile arena_data/derived/population_profile.json
```

For a smoke test on a large dataset:

```bash
python3 scripts/import_phh_dataset.py --input arena_data/external/phh --limit 1000
```

## Outputs

`arena_data/derived/phh_normalized.jsonl` contains one normalized hand per line.

`arena_data/derived/population_profile.json` contains aggregate population tendencies:

- fold rate
- call rate
- aggressive action rate
- showdown observed rate
- recommended exploit-rule multipliers

## Current Limitation

The first importer intentionally avoids depending on PokerKit or any network download. It parses PHH as TOML using Python's standard library and classifies actions conservatively from action strings. If you install PokerKit later, the parser can be upgraded to full semantic replay.

