from __future__ import annotations

from dataclasses import dataclass

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}
VALUE_RANK = {value: rank for rank, value in RANK_VALUE.items()}


@dataclass(frozen=True, order=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self) -> None:
        rank = self.rank.upper()
        suit = self.suit.lower()
        if rank not in RANKS:
            raise ValueError(f"Invalid card rank: {self.rank}")
        if suit not in SUITS:
            raise ValueError(f"Invalid card suit: {self.suit}")
        object.__setattr__(self, "rank", rank)
        object.__setattr__(self, "suit", suit)

    @property
    def value(self) -> int:
        return RANK_VALUE[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def parse_card(text: str) -> Card:
    token = text.strip()
    if len(token) != 2:
        raise ValueError(f"Cards must be two characters, got {text!r}")
    return Card(token[0], token[1])


def parse_cards(text: str | list[str] | tuple[str, ...]) -> list[Card]:
    if isinstance(text, str):
        tokens = text.replace(",", " ").split()
    else:
        tokens = list(text)
    return [parse_card(token) for token in tokens]


def full_deck(excluding: list[Card] | None = None) -> list[Card]:
    excluded = set(excluding or [])
    return [Card(rank, suit) for rank in RANKS for suit in SUITS if Card(rank, suit) not in excluded]


def canonical_hand(card_a: Card, card_b: Card) -> str:
    first, second = sorted([card_a, card_b], key=lambda card: card.value, reverse=True)
    if first.value == second.value:
        return first.rank + second.rank
    suited = "s" if first.suit == second.suit else "o"
    return first.rank + second.rank + suited

