#!/usr/bin/env python3
"""Opening-move analysis: top countries by minimax vs expected-average split."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geodle_core import countries_list, load_countries
from solve import score_guess


def rank_openings(universe: list[dict]) -> list[tuple[str, int, float]]:
    """Return (name, worst_case, expected) for every country."""
    ranked = []
    for guess in universe:
        worst, expected = score_guess(guess, universe)
        ranked.append((guess["name"], worst, expected))
    return ranked


def print_table(title: str, rows: list[tuple[str, int, float]], key_label: str) -> None:
    print(title)
    print(f"{'#':>3}  {'Country':<25}  {key_label:<12}  {'other':>10}")
    print("-" * 56)
    for i, (name, worst, expected) in enumerate(rows, 1):
        if key_label.startswith("worst"):
            print(f"{i:>3}  {name:<25}  {worst:<12}  {expected:>10.2f}")
        else:
            print(f"{i:>3}  {name:<25}  {expected:<12.2f}  {worst:>10}")
    print()


def bar_chart(
    ax: plt.Axes,
    names: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    color: str,
) -> None:
    y_pos = range(len(names) - 1, -1, -1)  # best at top
    ax.barh(list(y_pos), values[::-1], color=color, height=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names[::-1])
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    ax.set_xlim(0, max(values) * 1.15)
    for y, v in zip(y_pos, values[::-1]):
        ax.text(v + max(values) * 0.02, y, f"{v:.1f}" if isinstance(v, float) and v != int(v) else f"{int(v)}",
                va="center", fontsize=9)


def main() -> None:
    universe = countries_list(load_countries())
    scored = rank_openings(universe)

    by_minimax = sorted(scored, key=lambda r: (r[1], r[2], r[0]))[:10]
    by_average = sorted(scored, key=lambda r: (r[2], r[1], r[0]))[:10]

    print(f"Pool size: {len(universe)} countries\n")
    print_table(
        "Top 10 openings — minimax (minimize worst-case leftover)",
        by_minimax,
        "worst leftover",
    )
    # For average table, show expected as primary column
    print("Top 10 openings — average (minimize expected leftover)")
    print(f"{'#':>3}  {'Country':<25}  {'expected':<12}  {'worst':>10}")
    print("-" * 56)
    for i, (name, worst, expected) in enumerate(by_average, 1):
        print(f"{i:>3}  {name:<25}  {expected:<12.2f}  {worst:>10}")
    print()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Geodle opening guesses — top 10 by strategy", fontsize=13)

    bar_chart(
        ax1,
        [r[0] for r in by_minimax],
        [float(r[1]) for r in by_minimax],
        "Minimax (worst-case leftover)",
        "Worst-case countries remaining",
        "#4C78A8",
    )
    bar_chart(
        ax2,
        [r[0] for r in by_average],
        [r[2] for r in by_average],
        "Average (expected leftover)",
        "Expected countries remaining",
        "#F58518",
    )

    fig.tight_layout()
    out = "opening_analysis.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved chart to {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
