"""Game loop, dealing animation, and player interaction."""

from __future__ import annotations

import time

from rich.align import Align
from rich.console import Group
from rich.prompt import Prompt
from rich.text import Text

from . import ui
from .cards import Card, Shoe, hand_value, is_blackjack

console = ui.console

DEAL_DELAY = 0.16
FLIP_DELAY = 0.35
RESULT_DELAY = 0.4


class Hand:
    def __init__(self, bet: int = 0):
        self.cards: list[Card] = []
        self.bet = bet

    @property
    def total(self) -> int:
        return hand_value(self.cards)[0]

    @property
    def soft(self) -> bool:
        return hand_value(self.cards)[1]

    @property
    def busted(self) -> bool:
        return self.total > 21

    @property
    def blackjack(self) -> bool:
        return is_blackjack(self.cards)


class Table:
    def __init__(self, bankroll: int = 500):
        self.bankroll = bankroll
        self.shoe = Shoe(num_decks=4)
        self.player = Hand()
        self.dealer = Hand()
        self.hole_hidden = True
        self.message = Text("Place your bet to begin.", style="italic grey70")

    # ---------- rendering ----------

    def frame(self) -> Group:
        if self.hole_hidden and self.dealer.cards:
            up_total, up_soft = hand_value(self.dealer.cards[:1])
            dealer_score = ui.score_label(up_total, up_soft, False, False)
        else:
            dealer_score = ui.score_label(
                self.dealer.total, self.dealer.soft, self.dealer.busted, self.dealer.blackjack
            )
        player_score = ui.score_label(
            self.player.total, self.player.soft, self.player.busted, self.player.blackjack
        )

        hidden = {1} if (self.hole_hidden and len(self.dealer.cards) > 1) else set()

        dealer_block = Group(
            Align.center(Text("DEALER", style="bold grey62")),
            Align.center(ui.render_hand(self.dealer.cards, hidden_indices=hidden)),
            Align.center(dealer_score),
        )
        bet_label = f"YOU  ·  bet ${self.player.bet}" if self.player.bet else "YOU"
        player_block = Group(
            Align.center(Text(bet_label, style="bold grey62")),
            Align.center(ui.render_hand(self.player.cards)),
            Align.center(player_score),
        )

        bankroll_line = Text(justify="center")
        bankroll_line.append("bankroll ", style="grey50")
        bankroll_line.append(f"${self.bankroll}", style="bold gold3")

        title = Text("♠ ♥  B L A C K J A C K  ♦ ♣", style="bold grey78", justify="center")

        return Group(
            title,
            Text(""),
            dealer_block,
            Text(""),
            Align.center(Text("─" * 40, style="grey23")),
            Text(""),
            player_block,
            Text(""),
            Align.center(self.message),
            Text(""),
            bankroll_line,
        )

    def draw(self) -> None:
        console.clear()
        console.print(Align.center(self.frame()))

    # ---------- round flow ----------

    def new_round(self, bet: int) -> None:
        self.player = Hand(bet=bet)
        self.dealer = Hand()
        self.hole_hidden = True
        self.bankroll -= bet
        self.message = Text("Dealing...", style="italic grey70")
        self.draw()

        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
            time.sleep(0.1)

        deal_order = [self.player, self.dealer, self.player, self.dealer]
        for hand in deal_order:
            hand.cards.append(self.shoe.draw())
            self.draw()
            time.sleep(DEAL_DELAY)

        self.message = Text("", style="")

    def reveal_dealer(self) -> None:
        if not self.hole_hidden:
            return
        self.hole_hidden = False
        self.draw()
        time.sleep(FLIP_DELAY)

    def player_hit(self) -> None:
        self.player.cards.append(self.shoe.draw())
        self.message = Text("")
        self.draw()
        time.sleep(DEAL_DELAY)

    def dealer_play(self) -> None:
        self.reveal_dealer()
        while True:
            total, soft = hand_value(self.dealer.cards)
            if total > 21 or total > 17 or (total == 17 and not soft):
                break
            self.dealer.cards.append(self.shoe.draw())
            self.draw()
            time.sleep(DEAL_DELAY + 0.1)

    def settle(self) -> None:
        player, dealer = self.player, self.dealer
        bet = player.bet

        if player.blackjack and dealer.blackjack:
            outcome, payout = "Push — both blackjack.", bet
        elif player.blackjack:
            outcome, payout = "Blackjack! You win 3:2.", int(bet * 2.5)
        elif dealer.blackjack:
            outcome, payout = "Dealer has blackjack. You lose.", 0
        elif player.busted:
            outcome, payout = f"Bust with {player.total}. You lose.", 0
        elif dealer.busted:
            outcome, payout = f"Dealer busts with {dealer.total}. You win!", bet * 2
        elif player.total > dealer.total:
            outcome, payout = f"{player.total} beats {dealer.total}. You win!", bet * 2
        elif player.total < dealer.total:
            outcome, payout = f"{dealer.total} beats {player.total}. You lose.", 0
        else:
            outcome, payout = f"Push at {player.total}.", bet

        self.bankroll += payout
        win = payout > bet
        push = payout == bet
        style = "bold black on gold3" if win else ("bold white on grey54" if push else "bold white on red3")
        self.message = Text(f" {outcome} ", style=style)
        self.draw()
        time.sleep(RESULT_DELAY)


def ask_bet(bankroll: int) -> int:
    default = min(25, bankroll)
    while True:
        raw = Prompt.ask(
            f"[bold gold3]Bet[/] [grey58](bankroll ${bankroll}, 'q' to quit)[/]",
            default=str(default),
        )
        if raw.strip().lower() in ("q", "quit", "exit"):
            return -1
        try:
            bet = int(raw)
        except ValueError:
            console.print("[red]Enter a whole number.[/]")
            continue
        if bet <= 0:
            console.print("[red]Bet must be positive.[/]")
            continue
        if bet > bankroll:
            console.print("[red]You don't have that much.[/]")
            continue
        return bet


def ask_action(can_double: bool) -> str:
    opts = "h/hit, s/stand" + (", d/double" if can_double else "")
    while True:
        raw = Prompt.ask(f"[bold grey70]{opts}[/]").strip().lower()
        if raw in ("h", "hit"):
            return "hit"
        if raw in ("s", "stand"):
            return "stand"
        if can_double and raw in ("d", "double"):
            return "double"
        console.print("[red]Type h, s" + (", or d" if can_double else "") + ".[/]")


def play_round(table: Table) -> bool:
    """Play one full round. Returns False if the player wants to quit."""
    bet = ask_bet(table.bankroll)
    if bet == -1:
        return False

    table.new_round(bet)

    if table.player.blackjack or table.dealer.blackjack:
        table.reveal_dealer()
        table.settle()
        return True

    while True:
        can_double = len(table.player.cards) == 2 and table.bankroll >= table.player.bet
        table.draw()
        action = ask_action(can_double)

        if action == "hit":
            table.player_hit()
            if table.player.busted:
                break
        elif action == "double":
            table.bankroll -= table.player.bet
            table.player.bet *= 2
            table.player_hit()
            break
        else:  # stand
            break

    if not table.player.busted:
        table.dealer_play()

    table.settle()
    return True


def intro() -> None:
    word = "BLACKJACK"

    for revealed in range(len(ui.SUIT_ROW) + 1):
        console.clear()
        console.print(Text(""))
        console.print(ui.suit_row(revealed))
        time.sleep(0.18)

    for revealed in range(len(word) + 1):
        console.clear()
        console.print(ui.suit_row(len(ui.SUIT_ROW)))
        console.print(Text(""))
        console.print(ui.big_title(word, revealed, cursor_on=True))
        time.sleep(0.09)

    for blink_on in (False, True, False, True):
        console.clear()
        console.print(ui.suit_row(len(ui.SUIT_ROW)))
        console.print(Text(""))
        console.print(ui.big_title(word, len(word), cursor_on=blink_on))
        time.sleep(0.22)

    console.clear()
    console.print(ui.suit_row(len(ui.SUIT_ROW)))
    console.print(Text(""))
    console.print(ui.big_title(word, len(word), cursor_on=False))
    console.print(Align.center(Text("by torin", style="italic grey58")))
    time.sleep(0.9)


def run() -> None:
    intro()

    table = Table(bankroll=500)
    while table.bankroll > 0:
        if not play_round(table):
            break
    else:
        table.message = Text(" You're out of chips. ", style="bold white on red3")
        table.draw()

    console.clear()
    console.print(Align.center(Text(f"Final bankroll: ${table.bankroll}", style="bold gold3")))
    console.print(Align.center(Text("Thanks for playing.", style="italic grey62")))
