#!/usr/bin/env python3
"""Geodle practice — fixed opener, then multiple-choice for optimal round 2."""

from __future__ import annotations

import argparse
import random
import sys

from geodle import print_feedback
from geodle_core import countries_list, feedback, filter_possible, load_countries
from solve import best_guess, score_guess

OPENERS = ("Israel", "Gabon")
NUM_CHOICES = 4
STRATEGY = "expected"  # minimize expected leftover


def pick_choices(correct: dict, remaining: list[dict]) -> list[dict]:
    """Build a shuffled multiple-choice list from the remaining possible pool only."""
    pool_others = [c for c in remaining if c["name"] != correct["name"]]
    random.shuffle(pool_others)

    n_distractors = min(NUM_CHOICES - 1, len(pool_others))
    options = [correct] + pool_others[:n_distractors]
    random.shuffle(options)
    return options


def ask_choice(options: list[dict]) -> dict | None:
    letters = "ABCD"[: len(options)]
    print(
        "Which country is the optimal Round 2 guess "
        "(lowest expected leftover)?"
    )
    print()
    for letter, country in zip(letters, options):
        print(f"  {letter}) {country['name']}")
    print()

    prompt = f"Your answer ({letters[0]}–{letters[-1]}, or q to quit)> "
    while True:
        try:
            raw = input(prompt).strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw in {"q", "quit", "exit"}:
            return None
        if len(raw) == 1 and raw.upper() in letters:
            return options[letters.index(raw.upper())]
        for country in options:
            if country["name"].casefold() == raw:
                return country
        print(f"  Enter {', '.join(letters)}.")


def choose_opener(countries: dict[str, dict], requested: str | None) -> dict | None:
    if requested:
        key = requested.strip().casefold()
        matches = [name for name in OPENERS if name.casefold() == key or key in name.casefold()]
        if len(matches) == 1:
            return countries[matches[0].casefold()]
        print(f"Unknown opener {requested!r}. Choose from: {', '.join(OPENERS)}", file=sys.stderr)
        return None

    print("Choose Round 1 opener:")
    for i, name in enumerate(OPENERS, 1):
        print(f"  {i}) {name}")
    print()
    while True:
        try:
            raw = input("Opener (1/2 or name, q to quit)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw.casefold() in {"q", "quit", "exit"}:
            return None
        if raw in {"1", "2"}:
            return countries[OPENERS[int(raw) - 1].casefold()]
        for name in OPENERS:
            if name.casefold() == raw.casefold() or raw.casefold() in name.casefold():
                return countries[name.casefold()]
        print(f"  Enter 1, 2, or one of: {', '.join(OPENERS)}.")


def play_round(universe: list[dict], opener: dict) -> bool | None:
    """One practice round. Returns True/False for correct, None if quit."""
    candidates = [c for c in universe if c["name"] != opener["name"]]
    while True:
        secret = random.choice(candidates)
        observed = feedback(opener, secret)
        remaining = filter_possible(universe, opener, observed)
        if len(remaining) >= 2:
            break

    print("=" * 48)
    print(f"Round 1 is fixed: {opener['name']}")
    print_feedback(opener, secret)
    print(f"  ({len(remaining)} countries still possible)")
    print()

    optimal = best_guess(remaining, strategy=STRATEGY)
    worst, expected = score_guess(optimal, remaining)
    options = pick_choices(optimal, remaining)

    chosen = ask_choice(options)
    if chosen is None:
        return None

    if chosen["name"] == optimal["name"]:
        print()
        print(
            f"  Correct — {optimal['name']} minimizes expected leftover."
        )
        print(f"  (expected {expected:.2f}, worst {worst})")
        print()
        return True

    print()
    print(f"  Not quite. You picked {chosen['name']}.")
    print(f"  Optimal Round 2: {optimal['name']}")
    print(f"  (expected {expected:.2f}, worst {worst})")
    w2, e2 = score_guess(chosen, remaining)
    print(f"  Your pick scored expected={e2:.2f}, worst={w2}")
    print()
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Practice optimal Round 2 after a fixed opener")
    parser.add_argument(
        "opener",
        nargs="?",
        help="Round 1 country: Israel or Gabon (prompted if omitted)",
    )
    args = parser.parse_args(argv)

    countries = load_countries()
    universe = countries_list(countries)
    opener = choose_opener(countries, args.opener)
    if opener is None:
        return 0

    print()
    print(f"GEODLE PRACTICE — optimal Round 2 after {opener['name']}")
    print("Criterion: minimize expected leftover (not minimax).")
    print(f"You'll see {opener['name']}'s feedback, then pick the best next guess.")
    print()

    correct = 0
    total = 0
    while True:
        result = play_round(universe, opener)
        if result is None:
            break
        total += 1
        if result:
            correct += 1

        try:
            again = input("Another round? [Y/n]> ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if again in {"n", "no", "q", "quit"}:
            break
        print()

    if total:
        print(f"Score: {correct}/{total}")
    print("Bye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
