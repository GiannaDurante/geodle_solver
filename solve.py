#!/usr/bin/env python3
"""Optimal Geodle solver — minimax split of the remaining country pool."""

from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict

from geodle_core import (
    DATA_PATH,
    countries_list,
    feedback,
    filter_possible,
    load_countries,
)


def partition(guess: dict, remaining: list[dict]) -> dict[tuple, list[dict]]:
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for secret in remaining:
        buckets[feedback(guess, secret)].append(secret)
    return buckets


def score_guess(guess: dict, remaining: list[dict]) -> tuple[int, float]:
    """Return (max_bucket_size, expected_remaining_size).

    Expected remaining is the size-weighted average of bucket sizes:
    sum(size^2) / n — after observing feedback you stay in one bucket.
    """
    buckets = partition(guess, remaining)
    sizes = [len(b) for b in buckets.values()]
    n = len(remaining)
    max_bucket = max(sizes)
    expected = sum(s * s for s in sizes) / n
    return max_bucket, expected


def best_guess(remaining: list[dict], strategy: str = "minimax") -> dict:
    """Pick the guess in remaining with the best split.

    strategy:
      - "minimax": minimize worst-case leftover, then expected
      - "expected": minimize expected leftover, then worst-case
    """
    if len(remaining) == 1:
        return remaining[0]

    best: dict | None = None
    best_key: tuple | None = None
    for guess in remaining:
        max_bucket, expected = score_guess(guess, remaining)
        if strategy == "expected":
            key = (expected, max_bucket, guess["name"])
        else:
            key = (max_bucket, expected, guess["name"])
        if best_key is None or key < best_key:
            best_key = key
            best = guess
    assert best is not None
    return best


def solve_secret(secret: dict, universe: list[dict]) -> list[dict]:
    """Play optimally against secret; return the sequence of guesses."""
    remaining = list(universe)
    guesses: list[dict] = []
    while remaining:
        guess = best_guess(remaining)
        guesses.append(guess)
        observed = feedback(guess, secret)
        if observed == ("WIN",):
            break
        remaining = filter_possible(remaining, guess, observed)
        if not remaining:
            raise RuntimeError(
                f"Inconsistent state after guessing {guess['name']} "
                f"for secret {secret['name']}"
            )
    return guesses


def cmd_suggest(remaining: list[dict]) -> int:
    guess = best_guess(remaining)
    max_bucket, expected = score_guess(guess, remaining)
    print(f"Best guess: {guess['name']}")
    print(f"  remaining: {len(remaining)}")
    print(f"  worst-case leftover: {max_bucket}")
    print(f"  expected leftover:   {expected:.2f}")
    return 0


def cmd_auto(secret: dict, universe: list[dict]) -> int:
    remaining = list(universe)
    step = 0
    while True:
        guess = best_guess(remaining)
        step += 1
        max_bucket, expected = score_guess(guess, remaining)
        observed = feedback(guess, secret)
        print(
            f"#{step} guess={guess['name']}  "
            f"pool={len(remaining)}  "
            f"worst={max_bucket}  "
            f"expected={expected:.2f}"
        )
        if observed == ("WIN",):
            print(f"Solved {secret['name']} in {step} guess(es).")
            return 0
        remaining = filter_possible(remaining, guess, observed)
        print(f"       feedback kept {len(remaining)} possible")


def cmd_eval(universe: list[dict]) -> int:
    opening = best_guess(universe)
    max_bucket, expected = score_guess(opening, universe)
    print(f"Opening guess: {opening['name']}")
    print(f"  pool={len(universe)}  worst={max_bucket}  expected={expected:.2f}")
    print("Evaluating optimal play for every secret…")

    counts: list[int] = []
    worst_secret = ""
    worst_n = 0
    for i, secret in enumerate(sorted(universe, key=lambda c: c["name"]), 1):
        path = solve_secret(secret, universe)
        n = len(path)
        counts.append(n)
        if n > worst_n:
            worst_n = n
            worst_secret = secret["name"]
        if i % 25 == 0 or i == len(universe):
            print(f"  …{i}/{len(universe)}", flush=True)

    avg = sum(counts) / len(counts)
    dist: dict[int, int] = defaultdict(int)
    for n in counts:
        dist[n] += 1

    print()
    print(f"Secrets evaluated: {len(counts)}")
    print(f"Average guesses:   {avg:.3f}")
    print(f"Max guesses:       {worst_n} ({worst_secret})")
    print("Distribution:")
    for n in sorted(dist):
        print(f"  {n}: {dist[n]}")
    return 0


def find_by_name(countries: dict[str, dict], name: str) -> dict | None:
    key = name.strip().casefold()
    if key in countries:
        return countries[key]
    matches = [c for k, c in countries.items() if k.startswith(key) or key in k]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(sorted(c["name"] for c in matches)[:8])
        print(f"Ambiguous secret — did you mean: {names}?", file=sys.stderr)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optimal Geodle minimax solver")
    parser.add_argument(
        "mode",
        choices=("suggest", "auto", "eval"),
        help="suggest=best opening; auto=solve one secret; eval=all secrets",
    )
    parser.add_argument(
        "--secret",
        help="Secret country for auto mode (default: random)",
    )
    parser.add_argument(
        "--data",
        type=type(DATA_PATH),
        default=DATA_PATH,
        help="Path to countries.csv",
    )
    args = parser.parse_args(argv)

    if not args.data.exists():
        print(f"Missing data file: {args.data}", file=sys.stderr)
        return 1

    countries = load_countries(args.data)
    universe = countries_list(countries)

    if args.mode == "suggest":
        return cmd_suggest(universe)
    if args.mode == "eval":
        return cmd_eval(universe)

    # auto
    if args.secret:
        secret = find_by_name(countries, args.secret)
        if secret is None:
            print(f"Unknown country: {args.secret}", file=sys.stderr)
            return 1
    else:
        secret = random.choice(universe)
        print(f"(random secret chosen)")
    return cmd_auto(secret, universe)


if __name__ == "__main__":
    raise SystemExit(main())
