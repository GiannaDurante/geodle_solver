#!/usr/bin/env python3
"""Interactive Geodle assistant — enter site feedback, get the next best guess."""

from __future__ import annotations

import argparse
import sys

from geodle import find_country
from geodle_core import EXACT, HIGH, LOW, countries_list, filter_possible, load_countries
from solve import best_guess, score_guess

HELP = """
Enter what Geotrivia showed after your guess:
  continent / landlocked / borders  — y (match/yes) or n (wrong/no)
  temperature / population / land   — h higher, l lower, s same
    (h = site showed TOO LOW ↑, l = TOO HIGH ↓, s = exact match)

Commands: quit, list, pool
"""


def ask_yes_no(prompt: str) -> bool | None:
    while True:
        try:
            raw = input(f"{prompt} [y/n]> ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw in {"y", "yes", "match", "true", "1"}:
            return True
        if raw in {"n", "no", "wrong", "false", "0"}:
            return False
        print("  Enter y or n.")


def ask_cmp(label: str) -> str | None:
    """Return LOW/HIGH/EXACT from how the site compared guess vs secret."""
    while True:
        try:
            raw = input(
                f"{label} — secret higher, lower, or same? [h/l/s]> "
            ).strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        # Site "TOO LOW ↑" → guess below secret → secret is higher → LOW
        if raw in {"h", "high", "higher", "up", "↑", "too low"}:
            return LOW
        # Site "TOO HIGH ↓" → guess above secret → secret is lower → HIGH
        if raw in {"l", "lower", "down", "↓", "too high"}:
            return HIGH
        if raw in {"s", "same", "exact", "eq", "="}:
            return EXACT
        print("  Enter h (secret higher), l (secret lower), or s (same).")


def ask_feedback(guess: dict) -> tuple | None:
    print(f"Feedback for {guess['name']} (from geotrivia.com):")
    if ask_yes_no("  Solved — was this the secret country?") is True:
        return ("WIN",)

    continent = ask_yes_no("  Continent match?")
    if continent is None:
        return None
    landlocked = ask_yes_no("  Landlocked match?")
    if landlocked is None:
        return None
    borders = ask_yes_no("  Borders the secret?")
    if borders is None:
        return None
    temp = ask_cmp("  Temperature")
    if temp is None:
        return None
    pop = ask_cmp("  Population")
    if pop is None:
        return None
    land = ask_cmp("  Landmass")
    if land is None:
        return None

    return (continent, landlocked, borders, temp, pop, land)


def print_suggestion(remaining: list[dict], strategy: str) -> None:
    n = len(remaining)
    print(f"\nPool: {n} possible", end="")
    if n == 0:
        print(" — no countries match. Check feedback or data.")
        return
    if n == 1:
        print(f" — answer must be {remaining[0]['name']}.")
        return

    guess = best_guess(remaining, strategy=strategy)
    worst, expected = score_guess(guess, remaining)
    print()
    print(f"Suggested next guess ({strategy}): {guess['name']}")
    print(f"  expected leftover {expected:.2f}  ·  worst case {worst}")
    if n <= 12:
        names = ", ".join(sorted(c["name"] for c in remaining))
        print(f"  still possible: {names}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Geodle assistant — enter guesses and site feedback"
    )
    parser.add_argument(
        "--strategy",
        choices=("expected", "minimax"),
        default="expected",
        help="How to rank next guesses (default: expected)",
    )
    args = parser.parse_args(argv)

    countries = load_countries()
    universe = countries_list(countries)
    remaining = list(universe)
    turn = 0

    print("GEODLE ASSIST")
    print("Play at https://geotrivia.com/ — enter each guess and the site's feedback.")
    print(HELP.strip())
    print()

    while True:
        print_suggestion(remaining, args.strategy)

        if len(remaining) <= 1:
            if len(remaining) == 1:
                print(f"\nOnly {remaining[0]['name']} remains. Done.")
            break

        try:
            raw = input("\nYour guess (or quit/list/pool)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0

        if not raw:
            continue

        cmd = raw.casefold()
        if cmd in {"quit", "exit", "q"}:
            return 0
        if cmd == "list":
            print(", ".join(sorted(c["name"] for c in countries.values())))
            continue
        if cmd == "pool":
            print(", ".join(sorted(c["name"] for c in remaining)))
            continue
        if cmd == "help":
            print(HELP)
            continue

        guess = find_country(countries, raw)
        if guess is None:
            print("  Unknown country.")
            continue

        observed = ask_feedback(guess)
        if observed is None:
            return 0

        turn += 1

        if observed == ("WIN",):
            print(f"\nSolved in {turn} guess{'es' if turn != 1 else ''}!")
            return 0

        remaining = filter_possible(remaining, guess, observed)
        print(f"\n→ {len(remaining)} countries still possible")

        if not remaining:
            print(
                "  Empty pool — feedback may not match this dataset, "
                "or entries were mistyped."
            )


if __name__ == "__main__":
    raise SystemExit(main())
