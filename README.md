# Geodle Solver

Terminal clone and information-theoretic solver for **Geodle**, the daily geography game on [Geotrivia](https://geotrivia.com/).

This project is an independent analysis / practice tool and is not affiliated with Geotrivia. Play the real game at **[geotrivia.com](https://geotrivia.com/)**.

---

## Playing

```bash
python3 geodle.py
```

A secret country $S^\star$ is drawn uniformly from `countries.csv`. Each turn the player submits a guess $G$. The terminal reports $G$'s attributes and the comparison outcomes that Geodle exposes (continent and landlocked equality, adjacency to $S^\star$, and ordered comparisons on temperature, population, and land area). Commands: `list`, `quit`.

---

## Algorithm

Let $\mathcal{C}$ be the finite set of countries. The solver maintains a hypothesis set $R \subseteq \mathcal{C}$, initialized as $R \leftarrow \mathcal{C}$. Candidates are restricted to $R$ at every step (impossible countries are never guessed).

### Feedback function

Define $\mathrm{cmp}(x,y) \in \{\mathrm{LOW},\mathrm{HIGH},\mathrm{EXACT}\}$ by

$$
\mathrm{cmp}(x,y) =
\begin{cases}
\mathrm{LOW} & \text{if } x < y \\
\mathrm{HIGH} & \text{if } x > y \\
\mathrm{EXACT} & \text{if } x = y
\end{cases}
$$

and adjacency $\mathrm{adj}(A,B)$ iff $A$ and $B$ share a land border in the dataset.

If $G = S$, then $f(G,S) = (\mathrm{WIN})$. Otherwise

$$
\begin{aligned}
f(G,S) = \big(&
[G.\mathrm{continent} = S.\mathrm{continent}],\;
[G.\mathrm{landlocked} = S.\mathrm{landlocked}],\;
\mathrm{adj}(G,S), \\
&\;\mathrm{cmp}(G.T, S.T),\;
\mathrm{cmp}(G.P, S.P),\;
\mathrm{cmp}(G.A, S.A)
\big)
\end{aligned}
$$

where $T$, $P$, and $A$ are average temperature (°C), population, and landmass (km²).

### Partition induced by a guess

Given remaining set $R$ and candidate $G \in R$,

$$
\Pi(G; R) = \Big\{ \{ S \in R : f(G,S) = \sigma \} \;\Big|\; \sigma \in \{ f(G,S) : S \in R \} \Big\}.
$$

Let the block sizes be $s_1, \ldots, s_k$ with $\sum_i s_i = |R|$.

### Scores

$$
W(G; R) = \max_i s_i, \qquad
E(G; R) = \frac{1}{|R|} \sum_i s_i^2.
$$

$W$ is the worst-case residual size after observing $f(G, S^\star)$. $E$ is the expected residual size under the uniform prior $S^\star \sim \mathrm{Unif}(R)$.

### Selection rule

If $|R| = 1$, return that unique country. Otherwise choose

$$
G^\star(R) = \arg\min_{G \in R} \; \mathrm{key}(G; R)
$$

where the lexicographic key is

- **minimax strategy:** $\bigl(W(G;R),\; E(G;R),\; \mathrm{name}(G)\bigr)$
- **expected strategy:** $\bigl(E(G;R),\; W(G;R),\; \mathrm{name}(G)\bigr)$

$\mathrm{name}(G)$ breaks remaining ties alphabetically.

### Update

After playing $G$ and observing $\sigma = f(G, S^\star)$,

$$
R \leftarrow \{ S \in R : f(G,S) = \sigma \}.
$$

Repeat until $f(G, S^\star) = (\mathrm{WIN})$.

Implementation: `geodle_core.feedback`, `solve.partition`, `solve.score_guess`, `solve.best_guess`.

Under minimax on the full pool, the opening move is **Israel** ($W = 28$). Under expected residual, the opening move is **Gabon** ($E \approx 15.79$).

Precomputed scores for every Round 1 guess are in [`opening_scores.csv`](opening_scores.csv) (`worst_remaining`, `expected_remaining`, and ranks under each criterion).

---

## Commands

```bash
python3 geodle.py                          # play
python3 practice.py                        # R2 drill after Israel (expected criterion)
python3 solve.py suggest                   # opening move (minimax)
python3 solve.py auto --secret Japan       # optimal line vs a secret
python3 solve.py eval                      # aggregate optimal-play statistics
python3 opening_analysis.py                # top-10 openers (minimax & expected)
python3 decision_tree.py Israel            # R1→R2 tree for an opener
python3 round1_expected_histogram.py       # histogram of E(G; C) over all G
```

Requires Python 3; chart scripts require `matplotlib`.

---

## Credits

Geodle is a daily game published by [Geotrivia](https://geotrivia.com/). Country attributes in this repository are assembled estimates for solver research and may differ from the live game's dataset.
