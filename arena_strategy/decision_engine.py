from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .betting import Action, ActionType, legal_actions, stack_to_pot_ratio
from .board_texture import BoardTexture, classify_board
from .equity import estimate_equity
from .ev import simple_action_ev
from .evaluator import HandRank, evaluate_best
from .opponent_model import OpponentProfile
from .preflop import recommend_preflop
from .state_parser import TableState


@dataclass(frozen=True)
class CandidateAction:
    action: Action
    ev: float
    reason: str
    raw_ev: float | None = None


@dataclass(frozen=True)
class DecisionContext:
    hand_rank: HandRank | None
    equity: float
    board_texture: BoardTexture
    spr: float
    opponent_label: str | None
    legal_actions: list[Action]


@dataclass(frozen=True)
class Decision:
    action: Action
    candidates: list[CandidateAction]
    context: DecisionContext
    llm_review_used: bool = False


class StrategicReviewer(Protocol):
    def choose(self, context: DecisionContext, candidates: list[CandidateAction]) -> Action:
        """Select one of the already legal, EV-scored actions."""


class DecisionEngine:
    def __init__(self, simulations: int = 2000, seed: int | None = None, reviewer: StrategicReviewer | None = None) -> None:
        self.simulations = simulations
        self.seed = seed
        self.reviewer = reviewer

    def decide(self, state: TableState, opponent: OpponentProfile | None = None) -> Decision:
        actions = legal_actions(state.betting_state)
        texture = classify_board(state.board, state.preflop_aggressor)
        equity_result = estimate_equity(state.hero_cards, state.board, simulations=self.simulations, seed=self.seed)
        hand_rank = evaluate_best([*state.hero_cards, *state.board]) if len(state.board) >= 3 else None
        spr = stack_to_pot_ratio(state.hero_stack, state.pot)
        opponent_label = opponent.label if opponent else None

        context = DecisionContext(
            hand_rank=hand_rank,
            equity=equity_result.equity,
            board_texture=texture,
            spr=spr,
            opponent_label=opponent_label,
            legal_actions=actions,
        )

        preflop = recommend_preflop(state)
        if preflop is not None and self._preflop_action_is_allowed(preflop.action, state, actions):
            candidates = [
                CandidateAction(
                    action=preflop.action,
                    ev=0.0,
                    reason=f"Preflop chart gate ({preflop.chart}, {preflop.confidence} confidence): {preflop.reason}",
                    raw_ev=0.0,
                )
            ]
            for action in actions:
                if action != preflop.action:
                    candidates.append(
                        CandidateAction(
                            action=action,
                            ev=-1.0,
                            reason="Lower priority than deterministic preflop chart recommendation.",
                            raw_ev=-1.0,
                        )
                    )
            return Decision(action=preflop.action, candidates=candidates, context=context, llm_review_used=False)

        fold_equity = self._estimate_fold_equity(opponent)
        candidates = sorted(
            [self._score_action(action, equity_result.equity, state, texture, opponent_label, fold_equity, spr) for action in actions],
            key=lambda candidate: candidate.ev,
            reverse=True,
        )

        chosen = candidates[0].action
        llm_review_used = False
        if self.reviewer and len(candidates) > 1:
            reviewed = self.reviewer.choose(context, candidates[:3])
            if reviewed in actions:
                chosen = reviewed
                llm_review_used = True

        return Decision(action=chosen, candidates=candidates, context=context, llm_review_used=llm_review_used)

    def _preflop_action_is_allowed(self, action: Action, state: TableState, actions: list[Action]) -> bool:
        if action in actions:
            return True
        if action.amount < 0 or action.amount > state.hero_stack:
            return False
        legal_types = {legal.action_type for legal in actions}
        if action.action_type not in legal_types:
            return False
        if action.action_type == ActionType.BET:
            return state.to_call == 0 and action.amount >= max(state.big_blind, state.min_raise)
        if action.action_type == ActionType.RAISE:
            return state.to_call > 0 and action.amount >= state.to_call + state.min_raise
        if action.action_type == ActionType.CALL:
            return action.amount == min(state.to_call, state.hero_stack)
        return action.action_type in {ActionType.FOLD, ActionType.CHECK} and action.amount == 0

    def _score_action(
        self,
        action: Action,
        equity: float,
        state: TableState,
        texture: BoardTexture,
        opponent_label: str | None,
        fold_equity: float,
        spr: float,
    ) -> CandidateAction:
        raw_ev = simple_action_ev(action, equity, state.pot, state.to_call, fold_equity)
        penalty = self._sizing_penalty(action, equity, state, opponent_label, spr)
        adjusted_ev = raw_ev - penalty
        reason = self._reason(action, equity, texture, opponent_label)
        if penalty:
            reason = f"{reason} Sizing guard applied: -{penalty:.1f} EV."
        return CandidateAction(action=action, ev=adjusted_ev, reason=reason, raw_ev=raw_ev)

    def _sizing_penalty(
        self,
        action: Action,
        equity: float,
        state: TableState,
        opponent_label: str | None,
        spr: float,
    ) -> float:
        if action.action_type != ActionType.ALL_IN:
            return 0.0
        if state.hero_stack <= max(state.big_blind * 12, state.pot * 2):
            return 0.0

        premium_equity = 0.82
        strong_draw_or_value = equity >= 0.72 and spr <= 4.0
        credible_pressure = opponent_label == "nit" and equity >= 0.55 and spr <= 5.0
        if equity >= premium_equity or strong_draw_or_value or credible_pressure:
            return 0.0

        excess_spr = max(spr - 3.0, 0.0)
        equity_gap = max(0.70 - equity, 0.0)
        opponent_multiplier = 1.35 if opponent_label == "calling_station" else 1.0
        return (state.hero_stack * 0.45 + state.pot * excess_spr * 0.18 + state.hero_stack * equity_gap) * opponent_multiplier

    def _estimate_fold_equity(self, opponent: OpponentProfile | None) -> float:
        if opponent is None:
            return 0.25
        stats = opponent.stats
        if opponent.label == "calling_station":
            return 0.05
        if opponent.label == "nit":
            return min(0.65, 0.35 + stats.confidence * 0.25)
        return min(0.55, 0.20 + stats.fold_to_cbet * stats.confidence)

    def _reason(self, action: Action, equity: float, texture: object, opponent_label: str | None) -> str:
        if action.action_type == ActionType.FOLD:
            return "Zero-EV fallback when price or realization is poor."
        if action.action_type == ActionType.CHECK:
            return "Realizes equity without adding risk."
        if action.action_type == ActionType.CALL:
            return f"Calls with estimated equity {equity:.3f}."
        pressure = "low" if opponent_label == "calling_station" else "normal"
        return f"Applies {pressure} pressure with deterministic EV estimate."
