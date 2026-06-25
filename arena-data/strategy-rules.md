# Arena Poker Strategy Rules

- Hermes is the live arena operator.
- Codex is the offline strategy and code builder.
- Do not call Codex during a live action deadline unless absolutely necessary.
- Deterministic code owns legal actions, pot odds, equity, sizing, and ICM.
- LLM reasoning may only review already-legal candidate actions.
- Never bluff calling stations without a strong blocker or explicit pool read.
- Prefer low-variance lines early in tournaments.
- Increase pressure near bubbles only when fold equity is credible.
- Preserve stack in marginal spots where ICM pressure is high.
- Record every played or observed hand when practical.
- Every strategy-engine call should leave a line in `arena-data/decision-calls.jsonl`.
- Rebuild learning with `python -m arena_strategy.learning` after adding completed hand records.
- Check integration with `python scripts\check_integration.py`.
- Preflop uses conservative GTO-inspired chart gates. Do not override them loose during live action without a strong reason.
- Postflop favors legal, explainable, lower-variance lines unless equity and fold equity clearly justify aggression.

## Current Known Leak

The first Monte Carlo spot test showed the starter engine was too shove-heavy. A sizing guard now penalizes high-SPR all-ins unless equity, stack depth, or opponent fold tendencies justify them. Continue monitoring all-in results in the learning profile.
