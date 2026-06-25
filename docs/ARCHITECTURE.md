# Arena Poker Agent Architecture

This project separates deterministic poker computation from strategic review.

Deterministic modules own:

- Card parsing and hand evaluation
- Monte Carlo equity simulation
- Board texture classification
- Legal action generation
- Pot odds and action EV
- ICM approximations
- Opponent statistics and player-type probabilities

The LLM boundary is `StrategicReviewer` in `arena_strategy.decision_engine`. A reviewer may choose among the top already-legal, already-scored candidate actions, but it does not calculate equity, pot odds, hand rank, legal sizing, or ICM.

## Decision Pipeline

1. Parse table state into `TableState`.
2. Generate legal actions from `BettingState`.
3. Evaluate made hand when a board exists.
4. Estimate equity via seeded Monte Carlo simulation.
5. Classify board texture.
6. Compute stack-to-pot ratio.
7. Score every legal action with deterministic EV.
8. Optionally pass the top candidates to an LLM reviewer.
9. Return the chosen action and an explainable decision context.

## Next Build Steps

- Import real preflop charts and push/fold tables.
- Add range-vs-range equity instead of uniform unknown-villain sampling.
- Build a PHH parser and backtesting harness.
- Persist every decision context and result into structured hand records.
- Add solver-output comparison once licensed reference data is available.

