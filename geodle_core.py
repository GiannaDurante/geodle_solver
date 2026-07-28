#!/usr/bin/env python3
"""Shared Geodle data loading and feedback helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

DATA_PATH = Path(__file__).with_name("countries.csv")

# Numeric comparisons in feedback signatures
LOW = "LOW"
HIGH = "HIGH"
EXACT = "EXACT"


def load_countries(path: Path = DATA_PATH) -> dict[str, dict]:
    countries: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            neighbors = [
                n.strip()
                for n in (row["neighbors"] or "").split(";")
                if n.strip()
            ]
            country = {
                "name": row["country"],
                "iso3": row["iso3"],
                "continent": row["continent"],
                "landlocked": row["landlocked"].strip().lower() == "true",
                "neighbors": neighbors,
                "avg_temperature_c": float(row["avg_temperature_c"]),
                "population": int(float(row["population"])),
                "landmass_km2": float(row["landmass_km2"]),
            }
            countries[row["country"].casefold()] = country
    return countries


def countries_list(countries: dict[str, dict]) -> list[dict]:
    return list(countries.values())


def compare_num(guess: float, secret: float) -> str:
    if guess < secret:
        return LOW
    if guess > secret:
        return HIGH
    return EXACT


def borders(a: dict, b: dict) -> bool:
    return b["name"] in a["neighbors"] or a["name"] in b["neighbors"]


def feedback(guess: dict, secret: dict) -> tuple:
    """Hashable feedback signature for guess vs secret.

    When guess is the secret, returns a distinguished WIN token so the
    partition treats a correct guess separately from near-misses.
    """
    if guess["name"] == secret["name"]:
        return ("WIN",)

    return (
        guess["continent"] == secret["continent"],
        guess["landlocked"] == secret["landlocked"],
        borders(guess, secret),
        compare_num(guess["avg_temperature_c"], secret["avg_temperature_c"]),
        compare_num(guess["population"], secret["population"]),
        compare_num(guess["landmass_km2"], secret["landmass_km2"]),
    )


def filter_possible(
    remaining: Iterable[dict],
    guess: dict,
    observed: tuple,
) -> list[dict]:
    """Keep only countries consistent with observed feedback for guess."""
    return [c for c in remaining if feedback(guess, c) == observed]


def format_population(n: int) -> str:
    return f"{n:,}"


def format_landmass(km2: float) -> str:
    if km2 == int(km2):
        return f"{int(km2):,} km²"
    return f"{km2:,.1f} km²"


def compare_num_display(guess: float, secret: float) -> str:
    cmp = compare_num(guess, secret)
    if cmp == LOW:
        return "TOO LOW ↑"
    if cmp == HIGH:
        return "TOO HIGH ↓"
    return "EXACT"
