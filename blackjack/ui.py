"""Rendering: card art, table layout, and terminal animation helpers."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .cards import Card

console = Console()

CARD_W = 9
CARD_H = 7

RED = "bold red"
WHITE = "bold white"
DIM = "grey42"
GOLD = "bold gold3"
FELT = "on default"


BACK_WEAVE = [
    "◆·◆·◆·◆",
    "·◆·◆·◆·",
    "·◆·✦·◆·",
    "·◆·◆·◆·",
    "◆·◆·◆·◆",
]
BACK_GRADIENT = ["#4c1d95", "#7c3aed", "#a78bfa", "#7c3aed", "#4c1d95"]


def card_back_lines() -> list[Text]:
    """A diamond-lattice card back with a glowing emblem at its center."""
    inner = CARD_W - 2
    rows = [Text("╭" + "─" * inner + "╮", style=DIM)]
    for row_str, color in zip(BACK_WEAVE, BACK_GRADIENT):
        row = Text("│", style=DIM)
        for ch in row_str:
            if ch == "✦":
                row.append(ch, style="bold gold3")
            elif ch == "◆":
                row.append(ch, style=f"bold {color}")
            else:
                row.append(ch, style="grey27")
        row.append("│", style=DIM)
        rows.append(row)
    rows.append(Text("╰" + "─" * inner + "╯", style=DIM))
    return rows


def card_lines(card: Card | None, face_up: bool = True) -> list[Text]:
    """Return the CARD_H lines that make up a single card, face up or down."""
    if card is None:
        return [Text(" " * CARD_W) for _ in range(CARD_H)]

    if not face_up:
        return card_back_lines()

    style = RED if card.is_red else WHITE
    rank = card.rank
    suit = card.suit
    top_left = f"{rank}{suit}".ljust(2) if len(rank) == 1 else f"{rank}{suit}"
    bot_right = f"{rank}{suit}".rjust(2) if len(rank) == 1 else f"{rank}{suit}"

    inner_w = CARD_W - 2
    rows: list[Text] = []

    top_border = Text("╭" + "─" * inner_w + "╮", style=DIM)
    rows.append(top_border)

    line1 = Text("│", style=DIM)
    line1.append(top_left.ljust(inner_w), style=style)
    line1.append("│", style=DIM)
    rows.append(line1)

    def blank_row() -> Text:
        row = Text("│", style=DIM)
        row.append(" " * inner_w)
        row.append("│", style=DIM)
        return row

    rows.append(blank_row())

    mid = Text("│", style=DIM)
    suit_line = suit.center(inner_w)
    mid.append(suit_line, style=style)
    mid.append("│", style=DIM)
    rows.append(mid)

    rows.append(blank_row())

    line_last = Text("│", style=DIM)
    line_last.append(bot_right.rjust(inner_w), style=style)
    line_last.append("│", style=DIM)
    rows.append(line_last)

    bottom_border = Text("╰" + "─" * inner_w + "╯", style=DIM)
    rows.append(bottom_border)

    return rows


def render_hand(
    cards: list[Card],
    hidden_indices: set[int] | None = None,
    overlap: int = 5,
    gap: int = 1,
) -> Text:
    """Compose a hand of cards side-by-side into a single multi-line Text.

    Cards sit full-width with a small gap when the hand is short; once the
    hand grows past a handful of cards they start overlapping (like a
    tableau fan) so the row still fits the terminal.
    """
    hidden_indices = hidden_indices or set()
    if not cards:
        return Text("  (no cards)  ")

    all_lines = [
        card_lines(c, face_up=(i not in hidden_indices)) for i, c in enumerate(cards)
    ]
    fanning = len(cards) > 5

    result_rows: list[Text] = []
    for row_idx in range(CARD_H):
        row = Text()
        for card_idx, lines in enumerate(all_lines):
            piece = lines[row_idx]
            is_last = card_idx == len(all_lines) - 1
            if fanning and not is_last:
                row.append_text(piece[:overlap])
            else:
                row.append_text(piece)
                if not is_last:
                    row.append(" " * gap)
        result_rows.append(row)

    out = Text()
    for i, row in enumerate(result_rows):
        out.append_text(row)
        if i != len(result_rows) - 1:
            out.append("\n")
    return out


def score_label(total: int, soft: bool, busted: bool, blackjack: bool) -> Text:
    if blackjack:
        return Text(" BLACKJACK! ", style="bold black on gold3")
    if busted:
        return Text(f" BUST ({total}) ", style="bold white on red3")
    label = f" {'Soft ' if soft else ''}{total} "
    return Text(label, style="bold black on grey78")


def divider(title: str = "") -> None:
    console.rule(Text(title, style=GOLD) if title else "", style="grey30")


def clear() -> None:
    console.clear()


def typewriter(text: str, style: str = "bold gold3", delay: float = 0.012) -> None:
    import time

    for i in range(1, len(text) + 1):
        console.print(Text(text[:i], style=style), end="\r")
        time.sleep(delay)
    console.print(Text(text, style=style))


def banner() -> Panel:
    art = Text(justify="center")
    art.append("♠ ♥ ", style=RED)
    art.append("B L A C K J A C K", style="bold white")
    art.append(" ♦ ♣", style=RED)
    return Panel(Align.center(art), border_style="grey35", style=FELT, padding=(1, 4))


# ---------- big block title ----------

_BLOCK_FONT: dict[str, list[str]] = {
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "B": ["████ ", "█   █", "████ ", "█   █", "████ "],
    "C": [" ████", "█    ", "█    ", "█    ", " ████"],
    "J": ["  ███", "   █ ", "   █ ", "█  █ ", " ██  "],
    "K": ["█   █", "█  █ ", "███  ", "█  █ ", "█   █"],
    "L": ["█    ", "█    ", "█    ", "█    ", "█████"],
    " ": ["   ", "   ", "   ", "   ", "   "],
}
_FONT_ROWS = 5

SUIT_ROW = ["♠", "♥", "♦", "♣"]


def big_title(word: str, revealed: int, cursor_on: bool = True) -> Text:
    """Render `word` as large block letters, `revealed` letters shown so far.

    Letters alternate red/white like a deck of cards; a blinking cursor bar
    trails the last revealed letter while typing is still in progress.
    """
    letters = list(word)
    lines: list[Text] = [Text() for _ in range(_FONT_ROWS)]
    still_typing = revealed < len(letters)

    for i, ch in enumerate(letters):
        if i >= revealed:
            break
        pattern = _BLOCK_FONT.get(ch, _BLOCK_FONT[" "])
        style = WHITE if i % 2 == 0 else RED
        for row in range(_FONT_ROWS):
            lines[row].append(pattern[row], style=style)
            lines[row].append(" ")

    if still_typing:
        cursor_glyph = "█" if cursor_on else " "
        for row in range(_FONT_ROWS):
            lines[row].append(cursor_glyph, style="bold gold3")

    out = Text(justify="center")
    for i, line in enumerate(lines):
        out.append_text(line)
        if i != len(lines) - 1:
            out.append("\n")
    return out


def suit_row(revealed: int) -> Text:
    row = Text(justify="center")
    styles = [WHITE, RED, RED, WHITE]
    for i, s in enumerate(SUIT_ROW):
        if i < revealed:
            row.append(f"{s}   ", style=styles[i])
        else:
            row.append("    ")
    return row
