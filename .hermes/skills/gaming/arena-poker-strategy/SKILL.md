# Arena Poker Strategy

Hermes is the live arena operator. Codex is the offline strategy/code builder.

During live poker action deadlines:

- Prefer local deterministic strategy code over asking Codex.
- Do not call Codex unless the situation is non-urgent or genuinely blocked.
- Use `arena_strategy.decision.decide_action_dict(live_table_json)` for compact action guidance.
- Only submit actions that appear in the Arena legal-actions payload.
- Record live state, legal actions, chosen action, reasoning, and final result after the hand.
- Confirm integration by checking `arena-data/decision-calls.jsonl` or running `python scripts\check_integration.py`.
- In live play, trust the deterministic preflop chart gate over improvised preflop reasoning. These charts are conservative GTO-inspired defaults, not exact solver outputs.
- Do not widen preflop ranges from one result. Only adjust from aggregate repeated patterns.

Between hands or sessions, ask Codex to improve:

- `arena_strategy/decision.py`
- `arena_strategy/recorder.py`
- `arena_strategy/analyze.py`
- preflop ranges
- bet sizing rules
- opponent notes
- hand-history parsers
- legality tests
- leak reports
- `python -m arena_strategy.learning` to rebuild the learning profile from completed hand records

Important constraints:

- Deterministic code owns pot odds, equity, legal actions, sizing, hand evaluation, and ICM.
- LLM reasoning may only review already-legal, already-scored candidate actions.
- The engine includes a high-SPR shove guard, but all-in recommendations should still be monitored through recorded results and the learning profile.
- During live play, avoid hero calls, thin bluffs, and high-SPR stack-off lines unless deterministic equity, pot odds, opponent profile, and legal sizing all support the action.
