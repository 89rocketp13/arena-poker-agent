# Live Playing Protocol

This protocol is for live Arena use.

## Priority Order

1. Never submit an illegal action.
2. Preflop: use `arena_strategy.preflop` chart gate.
3. Postflop: use deterministic equity, board texture, SPR, EV scoring, and sizing guards.
4. Avoid high-SPR all-ins unless equity, stack depth, and opponent profile justify them.
5. Record every hand.
6. Learn slowly from aggregate data, not single hands.

## Live Loop

Before action:

```python
from arena_strategy.decision import decide_action_dict

decision = decide_action_dict(live_table_json)
```

Submit only:

```python
decision["action"]
decision["amount"]
```

Only submit if the action appears in the current legal-actions payload.

After hand completion:

- append a hand record with `arena_strategy.recorder.HandRecorder`
- include final `chip_delta` when available
- run `python3 -m arena_strategy.learning`

## Learning Confidence

- 1-20 hands: anecdotal only
- 20-100 hands: weak signal
- 100+ hands: usable tendency
- 500+ hands: strong read

Bad beats are not leaks by themselves. Won bluffs are not proof the bluff was good. Lost value bets are not proof the value bet was bad.

## Preflop Note

The included preflop ranges are conservative GTO-inspired defaults. They are not exact GTO Wizard or solver charts. Import real charts later if available.

