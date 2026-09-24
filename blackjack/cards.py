"""Card and Deck primitives for the blackjack game."""

from __future__ import annotations

import random
from dataclasses import dataclass

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]
RED_SUITS = {"♥", "♦"}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def is_red(self) -> bool:
        return self.suit in RED_SUITS

    @property
    def value(self) -> int:
        if self.rank == "A":
            return 11
        if self.rank in ("J", "Q", "K"):
            return 10
        return int(self.rank)

    @property
    def label(self) -> str:
        return f"{self.rank}{self.suit}"

    def __str__(self) -> str:
        return self.label


class Shoe:
    """A shuffled multi-deck shoe with a reshuffle threshold."""

    def __init__(self, num_decks: int = 4):
        self.num_decks = num_decks
        self._cards: list[Card] = []
        self.shuffle()

    def shuffle(self) -> None:
        self._cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in SUITS
            for rank in RANKS
        ]
        random.shuffle(self._cards)

    def needs_shuffle(self) -> bool:
        return len(self._cards) < (self.num_decks * 52) // 4

    def draw(self) -> Card:
        if not self._cards:
            self.shuffle()
        return self._cards.pop()


def hand_value(cards: list[Card]) -> tuple[int, bool]:
    """Return (best_value, is_soft) for a hand.

    A hand is "soft" if at least one ace is still being counted as 11.
    """
    total = sum(c.value for c in cards)
    aces_as_eleven = sum(1 for c in cards if c.rank == "A")
    while total > 21 and aces_as_eleven:
        total -= 10
        aces_as_eleven -= 1
    is_soft = aces_as_eleven > 0
    return total, is_soft


def is_blackjack(cards: list[Card]) -> bool:
    return len(cards) == 2 and hand_value(cards)[0] == 21
