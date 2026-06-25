# Monte Carlo Spot Performance Report

Generated with:

```powershell
python scripts\monte_carlo_performance.py --trials 120 --engine-sims 120 --seed 20260625
```

## Scope

This is a spot-level Monte Carlo test of the current `DecisionEngine`, not a full tournament simulation. Each scenario generates random hero cards and boards according to scenario filters, asks the decision module for an action, then realizes chip delta against a random heads-up opponent. Bets, raises, and all-ins use a simple opponent fold model:

- Unknown opponent: 25% fold chance
- Nit: 55% fold chance
- Calling station: 5% fold chance

## Summary

| Scenario | Trials | Avg Equity | Avg Estimated EV | Avg Realized Chip Delta | Actions |
| --- | ---: | ---: | ---: | ---: | --- |
| random_flop_single_raised_pot | 120 | 0.4758 | 1599.0312 | 960.0000 | all_in 52, raise 65, fold 3 |
| premium_preflop_vs_unknown | 120 | 0.8662 | 5763.6562 | 6010.0000 | all_in 120 |
| suited_broadway_flop_draw | 120 | 0.6432 | 2529.6438 | 1989.1667 | raise 32, all_in 88 |
| short_stack_pressure | 120 | 0.5233 | 482.5000 | 462.0833 | raise 54, all_in 66 |
| calling_station_postflop | 120 | 0.4989 | 1952.7833 | 2071.6667 | bet 66, all_in 54 |

## Read

The current module is profitable in these simplified chip-EV spot tests, but it is far too aggressive. The engine heavily prefers all-ins and minimum raises because the first EV model does not yet penalize overbet sizing, tournament life, range realization, or multi-street future value. The result is useful: the deterministic pipeline works, and the test harness is already catching the next strategic problem to solve.

## Recommended Next Fix

Add sizing-aware EV constraints before expanding simulation volume:

- Cap all-in selection when stack-to-pot ratio is high unless equity or fold equity crosses a strong threshold.
- Add ICM pressure into `DecisionEngine.decide`.
- Estimate villain call ranges instead of treating unknown villains as uniformly random hands.
- Add a baseline comparator such as fold/call/check-only or fixed TAG strategy.
- Increase run size after evaluator performance is optimized or replaced with a faster library.

