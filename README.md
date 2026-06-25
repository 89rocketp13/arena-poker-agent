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
