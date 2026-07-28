#!/usr/bin/env python3
"""Histogram of expected leftover after each possible Round 1 opening guess."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geodle_core import countries_list, load_countries
from solve import score_guess

MARK = "Switzerland"


def main() -> None:
    universe = countries_list(load_countries())
    n = len(universe)

    expected = []
    mark_value = None
    for guess in universe:
        _worst, exp = score_guess(guess, universe)
        expected.append(exp)
        if guess["name"] == MARK:
            mark_value = exp

    assert mark_value is not None
    expected_arr = np.array(expected)
    rank = int(np.sum(expected_arr < mark_value)) + 1  # 1 = best

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bins = np.linspace(expected_arr.min(), expected_arr.max(), 25)
    ax.hist(
        expected_arr,
        bins=bins,
        color="#4C78A8",
        edgecolor="white",
        linewidth=0.6,
    )

    ax.axvline(
        mark_value,
        color="#E45756",
        linewidth=2.0,
        linestyle="-",
        label=f"{MARK}: {mark_value:.2f}",
    )
    ymin, ymax = ax.get_ylim()
    ax.text(
        mark_value,
        ymax * 0.92,
        f"  {MARK}\n  E = {mark_value:.2f}\n  rank {rank}/{n}",
        color="#E45756",
        fontsize=10,
        va="top",
        ha="left",
    )

    ax.set_xlabel("Expected countries remaining after Round 1")
    ax.set_ylabel("Number of opening guesses")
    ax.set_title(
        "Distribution of Round 1 expected leftover\n"
        f"(all {n} countries as opener; lower is better)"
    )
    ax.legend(loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = "round1_expected_histogram.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"{MARK}: expected leftover = {mark_value:.2f}")
    print(f"Rank: {rank}/{n} (1 = best / lowest expected)")
    print(f"Best opener expected:  {expected_arr.min():.2f}")
    print(f"Median:                {np.median(expected_arr):.2f}")
    print(f"Worst opener expected: {expected_arr.max():.2f}")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
