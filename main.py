#!/usr/bin/env python3
from blackjack.game import run

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print()
