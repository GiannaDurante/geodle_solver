#!/usr/bin/env python3
"""Geodle — guess the secret country from geographic clues."""

from __future__ import annotations

import random
import sys

from geodle_core import (
    DATA_PATH,
    borders,
    compare_num_display,
    format_landmass,
    format_population,
    load_countries,
)


def find_country(countries: dict[str, dict], query: str) -> dict | None:
    key = query.strip().casefold()
    if key in countries:
        return countries[key]

    matches = [
        c
        for k, c in countries.items()
        if k.startswith(key) or key in k
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(sorted(c["name"] for c in matches)[:8])
        extra = "…" if len(matches) > 8 else ""
        print(f"  Ambiguous — did you mean: {names}{extra}?")
    return None


def print_feedback(guess: dict, secret: dict) -> bool:
    correct = guess["name"] == secret["name"]
    continent_ok = guess["continent"] == secret["continent"]
    landlocked_ok = guess["landlocked"] == secret["landlocked"]
    is_neighbor = borders(guess, secret)

    temp_cmp = compare_num_display(
        guess["avg_temperature_c"], secret["avg_temperature_c"]
    )
    pop_cmp = compare_num_display(guess["population"], secret["population"])
    land_cmp = compare_num_display(guess["landmass_km2"], secret["landmass_km2"])

    if correct:
        border_msg = "✓ that's the secret"
    elif is_neighbor:
        border_msg = "✓ borders the secret"
    else:
        border_msg = "✗ does not border the secret"

    print()
    print(f"  Guess: {guess['name']}")
    print(f"  ─────────────────────────────────────────")
    print(
        f"  Continent:   {guess['continent']:<16} "
        f"{'✓ MATCH' if continent_ok else '✗ wrong'}"
    )
    print(
        f"  Landlocked:  {str(guess['landlocked']):<16} "
        f"{'✓ MATCH' if landlocked_ok else '✗ wrong'}"
    )
    print(f"  Neighbors:   {border_msg}")
    print(
        f"  Temperature: {guess['avg_temperature_c']}°C"
        f"{'':<10} {temp_cmp}"
    )
    print(
        f"  Population:  {format_population(guess['population']):<16} {pop_cmp}"
    )
    print(
        f"  Landmass:    {format_landmass(guess['landmass_km2']):<16} {land_cmp}"
    )
    print()

    return correct


def main() -> int:
    if not DATA_PATH.exists():
        print(f"Missing data file: {DATA_PATH}", file=sys.stderr)
        return 1

    countries = load_countries(DATA_PATH)
    secret = random.choice(list(countries.values()))
    guesses = 0

    print("GEODLE — guess the secret country")
    print("Type a country name each turn. Commands: quit, list")
    print()

    while True:
        try:
            raw = input("Your guess> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0

        if not raw:
            continue

        cmd = raw.casefold()
        if cmd in {"quit", "exit", "q"}:
            print(f"The secret was {secret['name']}.")
            return 0
        if cmd == "list":
            print(", ".join(sorted(c["name"] for c in countries.values())))
            continue

        guess = find_country(countries, raw)
        if guess is None:
            print("  Unknown country. Try again (or type 'list').")
            continue

        guesses += 1
        if print_feedback(guess, secret):
            print(
                f"Correct! You got it in {guesses} "
                f"guess{'es' if guesses != 1 else ''}."
            )
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
