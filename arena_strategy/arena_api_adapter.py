from __future__ import annotations

from .betting import Action
from .decision_engine import DecisionEngine
from .opponent_model import OpponentProfile
from .state_parser import parse_table_state


class ArenaApiAdapter:
    """Boundary object for live Arena integration.

    The adapter intentionally accepts plain dictionaries so API-specific transport code can
    stay outside the decision engine.
    """

    def __init__(self, engine: DecisionEngine) -> None:
        self.engine = engine

    def choose_action(self, payload: dict, opponent: OpponentProfile | None = None) -> Action:
        state = parse_table_state(payload)
        return self.engine.decide(state, opponent).action

