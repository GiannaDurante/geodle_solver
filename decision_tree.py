#!/usr/bin/env python3
"""Decision tree: open with a country, then optimal round-2 guess per feedback."""

from __future__ import annotations

import argparse
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from geodle_core import EXACT, HIGH, LOW, countries_list, load_countries
from solve import best_guess, partition, score_guess

CONT_SHORT = {
    "Africa": "Afr",
    "Asia": "Asia",
    "Europe": "Eur",
    "North America": "NAm",
    "South America": "SAm",
    "Oceania": "Oce",
    "Antarctica": "Ant",
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")


def describe_feedback(fb: tuple, opener: dict) -> str:
    """Human-readable feedback after guessing opener (not a WIN)."""
    cont_ok, ll_ok, border, temp, pop, land = fb
    name = opener["name"]

    cont = (
        f"continent = {opener['continent']}"
        if cont_ok
        else f"continent ≠ {opener['continent']}"
    )
    if ll_ok:
        ll = "coastal" if not opener["landlocked"] else "landlocked"
    else:
        ll = "landlocked" if not opener["landlocked"] else "coastal"

    border_s = f"borders {name}" if border else "no border"

    temp_s = {
        LOW: f"warmer than {name}",
        HIGH: f"cooler than {name}",
        EXACT: "same temp",
    }[temp]
    pop_s = {
        LOW: "more people",
        HIGH: "fewer people",
        EXACT: "same pop",
    }[pop]
    land_s = {
        LOW: "more land",
        HIGH: "less land",
        EXACT: "same land",
    }[land]

    return f"{cont}\n{ll} · {border_s}\n{temp_s} · {pop_s} · {land_s}"


def short_feedback(fb: tuple, opener: dict) -> str:
    cont_ok, ll_ok, border, temp, pop, land = fb
    ctag = CONT_SHORT.get(opener["continent"], opener["continent"][:3])
    parts = []
    parts.append(ctag if cont_ok else f"¬{ctag}")
    if ll_ok:
        parts.append("coastal" if not opener["landlocked"] else "LL")
    else:
        parts.append("LL" if not opener["landlocked"] else "coastal")
    parts.append("border" if border else "¬border")
    parts.append({"LOW": "T↑", "HIGH": "T↓", "EXACT": "T="}[temp])
    parts.append({"LOW": "P↑", "HIGH": "P↓", "EXACT": "P="}[pop])
    parts.append({"LOW": "A↑", "HIGH": "A↓", "EXACT": "A="}[land])
    return " · ".join(parts)


def _cmp_order(cmp: str) -> int:
    """Order numeric feedback: higher-than-opener, equal, lower-than-opener."""
    return {LOW: 0, EXACT: 1, HIGH: 2}[cmp]


def secret_is_coastal(fb: tuple, opener: dict) -> bool:
    """Whether the secret is coastal, inferred from landlocked match feedback."""
    _, ll_ok, *_ = fb
    secret_landlocked = opener["landlocked"] if ll_ok else (not opener["landlocked"])
    return not secret_landlocked


def branch_sort_key(branch: dict, opener: dict) -> tuple:
    """Clump: ¬continent → coastal/LL → border → T → P → A."""
    fb = branch["feedback"]
    if fb == ("WIN",):
        return (2, 0, 0, 0, 0, 0, 0, 0)  # after all playable

    cont_ok, _ll_ok, border, temp, pop, land = fb
    # 0 = mismatch (¬Asia first), 1 = match
    cont_group = 0 if not cont_ok else 1
    # 0 = coastal, 1 = landlocked
    coastal_group = 0 if secret_is_coastal(fb, opener) else 1
    border_group = 0 if not border else 1
    return (
        cont_group,
        coastal_group,
        border_group,
        _cmp_order(temp),
        _cmp_order(pop),
        _cmp_order(land),
        -branch["size"],
        branch["r2"],
    )


def group_label(fb: tuple, opener: dict) -> str:
    ctag = CONT_SHORT.get(opener["continent"], opener["continent"][:3])
    cont_ok = fb[0]
    cont = ctag if cont_ok else f"¬{ctag}"
    coast = "coastal" if secret_is_coastal(fb, opener) else "landlocked"
    return f"{cont} · {coast}"


def build_tree(opener_name: str):
    universe = countries_list(load_countries())
    opener = next((c for c in universe if c["name"] == opener_name), None)
    if opener is None:
        # case-insensitive / unique substring
        matches = [c for c in universe if opener_name.casefold() in c["name"].casefold()]
        if len(matches) == 1:
            opener = matches[0]
        else:
            raise SystemExit(f"Unknown opener: {opener_name}")

    buckets = partition(opener, universe)
    branches = []
    for fb, remaining in buckets.items():
        if fb == ("WIN",):
            branches.append(
                {
                    "feedback": fb,
                    "label": "Exact match — solved",
                    "short": "WIN",
                    "size": 1,
                    "r2": opener["name"],
                    "worst": 0,
                    "expected": 0.0,
                    "names": [opener["name"]],
                }
            )
            continue
        r2 = best_guess(remaining)
        worst, expected = score_guess(r2, remaining)
        branches.append(
            {
                "feedback": fb,
                "label": describe_feedback(fb, opener),
                "short": short_feedback(fb, opener),
                "size": len(remaining),
                "r2": r2["name"],
                "worst": worst,
                "expected": expected,
                "names": sorted(c["name"] for c in remaining),
                "group": group_label(fb, opener),
            }
        )

    branches.sort(key=lambda b: branch_sort_key(b, opener))
    return opener, branches


def draw_tree(opener: dict, branches: list[dict], out: str) -> None:
    playable = [b for b in branches if b["feedback"] != ("WIN",)]
    n = len(playable)
    ctag = CONT_SHORT.get(opener["continent"], opener["continent"][:3])

    # Layout rows: group headers + branch rows (top → bottom)
    rows: list[tuple[str, dict | None]] = []
    prev_group = None
    for b in playable:
        if b["group"] != prev_group:
            rows.append(("header", b))
            prev_group = b["group"]
        rows.append(("branch", b))

    n_rows = len(rows)
    fig_h = max(10, 0.48 * n_rows + 2.8)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.6, n_rows + 1.2)
    ax.axis("off")

    ax.set_title(
        f"Geodle decision tree — Round 1: {opener['name']}\n"
        f"Ordered by ¬{ctag}/{ctag} → coastal/landlocked → border → T → P → A. "
        f"{n} outcomes · Round 2 = minimax.",
        fontsize=12,
        pad=12,
    )

    # Map row index → y; collect branch y's for root fan-out
    branch_ys: list[float] = []
    y_of: dict[int, float] = {}
    for i, (kind, b) in enumerate(rows):
        y = n_rows - 1 - i
        y_of[i] = y
        if kind == "branch":
            branch_ys.append(y)

    root_y = sum(branch_ys) / len(branch_ys) if branch_ys else n_rows / 2
    root = FancyBboxPatch(
        (0.25, root_y - 0.35),
        2.1,
        0.7,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        facecolor="#4C78A8",
        edgecolor="#333333",
        linewidth=1.2,
    )
    ax.add_patch(root)
    ax.text(
        1.3,
        root_y,
        f"R1: {opener['name']}",
        ha="center",
        va="center",
        color="white",
        fontsize=11,
        fontweight="bold",
    )

    for i, (kind, b) in enumerate(rows):
        y = y_of[i]
        if kind == "header":
            ax.text(
                3.4,
                y,
                b["group"],
                ha="left",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="#333333",
            )
            ax.plot([3.4, 9.7], [y - 0.28, y - 0.28], color="#CCCCCC", linewidth=0.8)
            continue

        ax.plot([2.35, 3.4], [root_y, y], color="#BBBBBB", linewidth=0.7, zorder=0)

        fb_box = FancyBboxPatch(
            (3.4, y - 0.36),
            3.5,
            0.72,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor="#F0F0F0",
            edgecolor="#888888",
            linewidth=0.8,
        )
        ax.add_patch(fb_box)
        ax.text(
            5.15,
            y + 0.10,
            b["short"],
            ha="center",
            va="center",
            fontsize=7.5,
            family="monospace",
        )
        ax.text(
            5.15,
            y - 0.16,
            f"pool → {b['size']}",
            ha="center",
            va="center",
            fontsize=8,
            color="#444444",
        )

        ax.annotate(
            "",
            xy=(7.3, y),
            xytext=(6.95, y),
            arrowprops=dict(arrowstyle="->", color="#666666", lw=0.9),
        )

        r2_box = FancyBboxPatch(
            (7.3, y - 0.33),
            2.4,
            0.66,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor="#F58518",
            edgecolor="#333333",
            linewidth=1.0,
        )
        ax.add_patch(r2_box)
        ax.text(
            8.5,
            y + 0.07,
            f"R2: {b['r2']}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )
        ax.text(
            8.5,
            y - 0.16,
            f"worst {b['worst']} · E[{b['expected']:.1f}]",
            ha="center",
            va="center",
            fontsize=7.5,
            color="white",
        )

    ax.text(
        0.3,
        -0.4,
        f"Legend: {ctag}/¬{ctag} = continent · coastal/LL = landlocked · "
        f"T/P/A ↑ = secret higher than {opener['name']}",
        fontsize=8,
        color="#555555",
        va="top",
    )

    fig.tight_layout()
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


def print_tree(opener: dict, branches: list[dict]) -> None:
    print(f"Round 1: {opener['name']}")
    print(f"{'pool':>4}  {'round-2 guess':<25}  feedback")
    print("-" * 90)
    prev_group = None
    for b in branches:
        if b["feedback"] == ("WIN",):
            print(f"{'1':>4}  {'(solved)':<25}  WIN — secret is {opener['name']}")
            continue
        if b["group"] != prev_group:
            print(f"\n  [{b['group']}]")
            prev_group = b["group"]
        print(f"{b['size']:>4}  {b['r2']:<25}  {b['short']}")
    print()


def write_text(opener: dict, branches: list[dict], out: str) -> None:
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"Decision tree after opening with {opener['name']}\n")
        f.write("Ordered: ¬continent → coastal/LL → border → T → P → A\n")
        f.write("=" * 72 + "\n\n")
        prev_group = None
        for b in branches:
            if b["feedback"] == ("WIN",):
                f.write(f"Pool 1: WIN\n  → Solved on round 1\n\n")
                continue
            if b["group"] != prev_group:
                f.write(f"## {b['group']}\n\n")
                prev_group = b["group"]
            f.write(f"Pool {b['size']}: {b['short']}\n")
            f.write(
                f"  → Optimal R2: {b['r2']}  "
                f"(worst={b['worst']}, expected={b['expected']:.2f})\n"
            )
            f.write(f"  Remaining: {', '.join(b['names'])}\n\n")
    print(f"Saved {out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R1 → R2 minimax decision tree")
    parser.add_argument(
        "opener",
        nargs="?",
        default="Gabon",
        help="Opening country (default: Gabon)",
    )
    args = parser.parse_args(argv)

    opener, branches = build_tree(args.opener)
    base = f"{slug(opener['name'])}_decision_tree"
    print_tree(opener, branches)
    draw_tree(opener, branches, f"{base}.png")
    write_text(opener, branches, f"{base}.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
