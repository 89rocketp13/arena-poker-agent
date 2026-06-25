from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arena_strategy.betting import ActionType
from arena_strategy.cards import Card, full_deck
from arena_strategy.decision_engine import DecisionEngine
from arena_strategy.evaluator import compare_hands
from arena_strategy.opponent_model import OpponentProfile
from arena_strategy.state_parser import TableState


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    board_cards: int
    pot: int
    to_call: int
    hero_stack: int
    min_raise: int
    big_blind: int
    position: str
    opponent_kind: str
    hero_filter: str


SCENARIOS = [
    Scenario(
        name="random_flop_single_raised_pot",
        description="Random flop, medium stack, single opponent, facing a small bet.",
        board_cards=3,
        pot=1200,
        to_call=300,
        hero_stack=9000,
        min_raise=600,
        big_blind=200,
        position="button",
        opponent_kind="unknown",
        hero_filter="any",
    ),
    Scenario(
        name="premium_preflop_vs_unknown",
        description="Premium pair preflop with no bet to call.",
        board_cards=0,
        pot=300,
        to_call=0,
        hero_stack=10000,
        min_raise=400,
        big_blind=200,
        position="cutoff",
        opponent_kind="unknown",
        hero_filter="premium_pair",
    ),
    Scenario(
        name="suited_broadway_flop_draw",
        description="Suited broadway hand on a random flop, facing a half-pot-ish bet.",
        board_cards=3,
        pot=1600,
        to_call=700,
        hero_stack=8500,
        min_raise=1400,
        big_blind=200,
        position="button",
        opponent_kind="nit",
        hero_filter="suited_broadway",
    ),
    Scenario(
        name="short_stack_pressure",
        description="Short stack preflop decision with fold equity available.",
        board_cards=0,
        pot=500,
        to_call=200,
        hero_stack=2200,
        min_raise=400,
        big_blind=200,
        position="small_blind",
        opponent_kind="nit",
        hero_filter="any",
    ),
    Scenario(
        name="calling_station_postflop",
        description="Postflop spot against a calling-station profile.",
        board_cards=3,
        pot=1400,
        to_call=0,
        hero_stack=7600,
        min_raise=400,
        big_blind=200,
        position="hijack",
        opponent_kind="calling_station",
        hero_filter="any",
    ),
]


def build_profile(kind: str) -> OpponentProfile | None:
    if kind == "unknown":
        return None
    profile = OpponentProfile(kind)
    if kind == "nit":
        for _ in range(80):
            profile.update_hand(vpip=False, pfr=False, folded_to_cbet=True, saw_showdown=False)
        for _ in range(12):
            profile.update_hand(vpip=True, pfr=True, folded_to_cbet=False, saw_showdown=False)
    elif kind == "calling_station":
        for _ in range(80):
            profile.update_hand(vpip=True, pfr=False, folded_to_cbet=False, saw_showdown=True)
    else:
        raise ValueError(f"Unsupported opponent kind: {kind}")
    return profile


def draw_cards(rng: random.Random, count: int, excluded: list[Card] | None = None) -> list[Card]:
    return rng.sample(full_deck(excluded or []), count)


def draw_hero_cards(rng: random.Random, hero_filter: str) -> list[Card]:
    while True:
        cards = draw_cards(rng, 2)
        values = sorted([card.value for card in cards], reverse=True)
        suited = cards[0].suit == cards[1].suit
        if hero_filter == "any":
            return cards
        if hero_filter == "premium_pair" and values[0] == values[1] and values[0] >= 12:
            return cards
        if hero_filter == "suited_broadway" and suited and min(values) >= 10:
            return cards


def realize_chip_delta(
    rng: random.Random,
    hero_cards: list[Card],
    board: list[Card],
    action_type: ActionType,
    action_amount: int,
    pot: int,
    to_call: int,
    opponent_kind: str,
) -> int:
    if action_type == ActionType.FOLD:
        return 0
    if action_type in {ActionType.BET, ActionType.RAISE, ActionType.ALL_IN}:
        fold_chance = {"unknown": 0.25, "nit": 0.55, "calling_station": 0.05}.get(opponent_kind, 0.25)
        if rng.random() < fold_chance:
            return pot

    known = [*hero_cards, *board]
    villain_cards = draw_cards(rng, 2, known)
    runout = draw_cards(rng, 5 - len(board), [*known, *villain_cards])
    final_board = [*board, *runout]
    result = compare_hands(hero_cards, villain_cards, final_board)

    invested = action_amount if action_type in {ActionType.CALL, ActionType.BET, ActionType.RAISE, ActionType.ALL_IN} else 0
    villain_match = invested if action_type in {ActionType.BET, ActionType.RAISE, ActionType.ALL_IN} else 0
    if result > 0:
        return pot + villain_match
    if result < 0:
        return -invested
    return (pot + villain_match - invested) // 2


def run_scenario(scenario: Scenario, trials: int, engine_sims: int, seed: int) -> dict:
    rng = random.Random(seed)
    engine = DecisionEngine(simulations=engine_sims, seed=seed)
    opponent = build_profile(scenario.opponent_kind)
    action_counts: Counter[str] = Counter()
    evs: list[float] = []
    equities: list[float] = []
    realized: list[int] = []
    samples: list[dict] = []

    for trial in range(trials):
        hero_cards = draw_hero_cards(rng, scenario.hero_filter)
        board = draw_cards(rng, scenario.board_cards, hero_cards)
        state = TableState(
            hero_cards=hero_cards,
            board=board,
            pot=scenario.pot,
            to_call=scenario.to_call,
            hero_stack=scenario.hero_stack,
            min_raise=scenario.min_raise,
            big_blind=scenario.big_blind,
            position=scenario.position,
            opponents_in_hand=1,
            preflop_aggressor="hero",
        )
        decision = engine.decide(state, opponent)
        action_counts[decision.action.action_type.value] += 1
        evs.append(decision.candidates[0].ev)
        equities.append(decision.context.equity)
        delta = realize_chip_delta(
            rng,
            hero_cards,
            board,
            decision.action.action_type,
            decision.action.amount,
            scenario.pot,
            scenario.to_call,
            scenario.opponent_kind,
        )
        realized.append(delta)
        if trial < 8:
            samples.append(
                {
                    "hero_cards": [str(card) for card in hero_cards],
                    "board": [str(card) for card in board],
                    "action": decision.action.action_type.value,
                    "amount": decision.action.amount,
                    "equity": round(decision.context.equity, 4),
                    "estimated_best_ev": round(decision.candidates[0].ev, 2),
                    "realized_chip_delta": delta,
                    "top_candidates": [
                        {
                            "action": candidate.action.action_type.value,
                            "amount": candidate.action.amount,
                            "ev": round(candidate.ev, 2),
                        }
                        for candidate in decision.candidates[:3]
                    ],
                }
            )

    positive = sum(1 for value in realized if value > 0)
    negative = sum(1 for value in realized if value < 0)
    neutral = trials - positive - negative
    return {
        "scenario": asdict(scenario),
        "trials": trials,
        "engine_equity_simulations_per_decision": engine_sims,
        "seed": seed,
        "action_frequencies": dict(action_counts),
        "average_estimated_best_ev": round(mean(evs), 4),
        "average_estimated_equity": round(mean(equities), 4),
        "average_realized_chip_delta": round(mean(realized), 4),
        "positive_realized_rate": round(positive / trials, 4),
        "negative_realized_rate": round(negative / trials, 4),
        "neutral_realized_rate": round(neutral / trials, 4),
        "sample_decisions": samples,
    }


def write_csv(results: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario",
                "trials",
                "average_estimated_best_ev",
                "average_estimated_equity",
                "average_realized_chip_delta",
                "positive_realized_rate",
                "negative_realized_rate",
                "neutral_realized_rate",
                "action_frequencies",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "scenario": result["scenario"]["name"],
                    "trials": result["trials"],
                    "average_estimated_best_ev": result["average_estimated_best_ev"],
                    "average_estimated_equity": result["average_estimated_equity"],
                    "average_realized_chip_delta": result["average_realized_chip_delta"],
                    "positive_realized_rate": result["positive_realized_rate"],
                    "negative_realized_rate": result["negative_realized_rate"],
                    "neutral_realized_rate": result["neutral_realized_rate"],
                    "action_frequencies": json.dumps(result["action_frequencies"], sort_keys=True),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Monte Carlo spot-performance harness for the Arena decision engine.")
    parser.add_argument("--trials", type=int, default=500, help="Decision spots per scenario.")
    parser.add_argument("--engine-sims", type=int, default=400, help="Equity simulations inside each decision.")
    parser.add_argument("--seed", type=int, default=20260625)
    parser.add_argument("--out-dir", type=Path, default=Path("arena_data/simulations"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = [
        run_scenario(scenario, trials=args.trials, engine_sims=args.engine_sims, seed=args.seed + idx)
        for idx, scenario in enumerate(SCENARIOS)
    ]

    json_path = args.out_dir / "monte_carlo_performance.json"
    csv_path = args.out_dir / "monte_carlo_performance_summary.csv"
    json_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    write_csv(results, csv_path)

    for result in results:
        name = result["scenario"]["name"]
        avg = result["average_realized_chip_delta"]
        equity = result["average_estimated_equity"]
        actions = result["action_frequencies"]
        print(f"{name}: avg_realized={avg}, avg_equity={equity}, actions={actions}")
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
