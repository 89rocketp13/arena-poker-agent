# Arena Poker Agent

Hybrid tournament poker engine where deterministic Python modules handle poker math and an optional strategy reviewer handles adaptation.

## Quick Start

```powershell
python -m pytest
```

## Example

```python
from arena_strategy.decision_engine import DecisionEngine
from arena_strategy.state_parser import parse_table_state

state = parse_table_state({
    "hero_cards": ["Ah", "Kh"],
    "board": ["Qh", "Jh", "2c"],
    "pot": 1200,
    "to_call": 300,
    "hero_stack": 9000,
    "min_raise": 600,
    "big_blind": 200,
    "position": "button",
    "opponents_in_hand": 1,
    "preflop_aggressor": "hero"
})

decision = DecisionEngine(simulations=1000, seed=7).decide(state)
print(decision.action)
print(decision.context.equity)
```

## Hermes Integration Check

```powershell
python scripts\check_integration.py
```

If Hermes/Claude is calling the strategy facade, `arena-data/decision-calls.jsonl` will grow. Completed hand records can be converted into an adaptive learning profile with:

```powershell
python -m arena_strategy.learning
```

## PHH Dataset Import

Place University of Toronto CPRG PHH files under `arena_data/external/phh/`, then run:

```powershell
python scripts\import_phh_dataset.py --input arena_data\external\phh
```

See [docs/PHH_DATASET.md](docs/PHH_DATASET.md).

## Live Decision Safety

Preflop decisions are now gated through `arena_strategy.preflop` before Monte Carlo EV scoring. These are conservative, GTO-inspired starter ranges, not exact paid-solver charts. Replace them with imported solver ranges when available.

For live use:

- Preflop: use the deterministic chart recommendation.
- Postflop: use equity, board texture, SPR, EV scoring, and shove guard.
- Always verify returned actions against the table's legal actions.
- Record every hand and learn only from aggregate samples.
