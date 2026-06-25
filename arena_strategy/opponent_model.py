from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OpponentStats:
    hands_observed: int = 0
    vpip_count: int = 0
    pfr_count: int = 0
    three_bet_count: int = 0
    cbet_faced: int = 0
    fold_to_cbet_count: int = 0
    turn_faced: int = 0
    fold_turn_count: int = 0
    river_faced: int = 0
    fold_river_count: int = 0
    river_aggression_count: int = 0
    showdown_count: int = 0

    def rate(self, count: int, denominator: int | None = None) -> float:
        denom = denominator if denominator is not None else self.hands_observed
        return 0.0 if denom <= 0 else count / denom

    @property
    def vpip(self) -> float:
        return self.rate(self.vpip_count)

    @property
    def pfr(self) -> float:
        return self.rate(self.pfr_count)

    @property
    def three_bet(self) -> float:
        return self.rate(self.three_bet_count)

    @property
    def fold_to_cbet(self) -> float:
        return self.rate(self.fold_to_cbet_count, self.cbet_faced)

    @property
    def confidence(self) -> float:
        return min(1.0, self.hands_observed / 100.0)


PLAYER_TYPES = ("nit", "tag", "lag", "loose_passive", "calling_station", "maniac")


@dataclass
class OpponentProfile:
    player_id: str
    stats: OpponentStats = field(default_factory=OpponentStats)
    type_probabilities: dict[str, float] = field(default_factory=lambda: {kind: 1 / len(PLAYER_TYPES) for kind in PLAYER_TYPES})

    @property
    def label(self) -> str:
        return max(self.type_probabilities.items(), key=lambda item: item[1])[0]

    def update_hand(
        self,
        vpip: bool,
        pfr: bool,
        three_bet: bool = False,
        folded_to_cbet: bool | None = None,
        saw_showdown: bool = False,
        river_aggressive: bool = False,
    ) -> None:
        self.stats.hands_observed += 1
        self.stats.vpip_count += int(vpip)
        self.stats.pfr_count += int(pfr)
        self.stats.three_bet_count += int(three_bet)
        if folded_to_cbet is not None:
            self.stats.cbet_faced += 1
            self.stats.fold_to_cbet_count += int(folded_to_cbet)
        self.stats.showdown_count += int(saw_showdown)
        self.stats.river_aggression_count += int(river_aggressive)
        self.type_probabilities = classify_player(self.stats)


def classify_player(stats: OpponentStats) -> dict[str, float]:
    vpip = stats.vpip
    pfr = stats.pfr
    gap = max(vpip - pfr, 0.0)
    aggression = stats.rate(stats.river_aggression_count)
    showdown = stats.rate(stats.showdown_count)

    scores = {
        "nit": (1 - vpip) * 1.5 + (1 - pfr),
        "tag": (1 - abs(vpip - 0.22) * 3) + (1 - abs(pfr - 0.18) * 3),
        "lag": vpip + pfr + stats.three_bet,
        "loose_passive": vpip + gap * 1.5 + (1 - aggression),
        "calling_station": vpip + showdown + (1 - stats.fold_to_cbet),
        "maniac": vpip + pfr + aggression + stats.three_bet * 2,
    }
    clipped = {label: max(score, 0.01) for label, score in scores.items()}
    total = sum(clipped.values())
    return {label: score / total for label, score in clipped.items()}

