"""
CQI Replication Analysis

Reproduces all statistical tests from:
  Chan (2026). "Evaluating MindForest's AI Therapy Readiness Using LLM-as-Judge"

Usage:
  python analyze.py                              # Use included data
  python analyze.py --data path/to/scores.csv    # Use your own CQI scores

Output: Markdown report to stdout.

Requirements: numpy, scipy (see requirements.txt)
"""

import argparse
import csv
import os
import numpy as np
from scipy import stats

DIMS = ["CS", "FD", "CP", "CN", "TD", "TC"]
ALL_DIMS = ["CS", "FD", "CP", "CN", "TD", "TC", "DF"]
DIM_NAMES = {
    "CS": "Clinical Skillfulness",
    "FD": "Facilitative Depth",
    "CP": "Contextual Precision",
    "CN": "Conversational Naturalness",
    "TD": "Therapeutic Direction",
    "TC": "Therapeutic Containment",
    "DF": "Dark Factor (6=clean)",
    "CQI": "CQI (Composite)",
}


def cronbachs_alpha(matrix):
    """Compute Cronbach's alpha for a score matrix (rows=items, cols=dimensions)."""
    k = matrix.shape[1]
    if k < 2:
        return float("nan")
    item_vars = matrix.var(axis=0, ddof=1)
    total_var = matrix.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return (k / (k - 1)) * (1 - item_vars.sum() / total_var)


def cohens_d(group1, group2):
    """Compute Cohen's d with pooled standard deviation."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float("nan")
    pooled = np.sqrt(
        (np.var(group1, ddof=1) * (n1 - 1) + np.var(group2, ddof=1) * (n2 - 1))
        / (n1 + n2 - 2)
    )
    if pooled == 0:
        return float("nan")
    return (np.mean(group1) - np.mean(group2)) / pooled


def cohens_d_ci(d, n1, n2, alpha=0.05):
    """95% CI for Cohen's d via non-central t approximation."""
    se = np.sqrt(n1 + n2) / np.sqrt(n1 * n2) * np.sqrt(1 + d**2 * n1 * n2 / (2 * (n1 + n2)))
    z = stats.norm.ppf(1 - alpha / 2)
    return d - z * se, d + z * se


def load_csv(path):
    """Load CQI scores from CSV."""
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for d in ALL_DIMS:
                row[d] = int(row[d])
            row["CQI"] = float(row["CQI"])
            rows.append(row)
    return rows


def sig_label(p):
    if p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    elif p < 0.10:
        return "\u2020"
    return ""


def analyze(rows):
    report = []
    report.append("# CQI Replication Report\n")
    report.append(f"n = {len(rows)} windows\n")

    # --- 1. Score Distributions ---
    report.append("## 1. Score Distributions\n")
    report.append("| Dimension | Mean | SD | Min | Max |")
    report.append("|-----------|------|----|-----|-----|")
    for d in ALL_DIMS + ["CQI"]:
        scores = [r[d] for r in rows]
        report.append(
            f"| {DIM_NAMES.get(d, d)} | {np.mean(scores):.2f} | "
            f"{np.std(scores, ddof=1):.2f} | {min(scores)} | {max(scores)} |"
        )
    report.append("")

    # --- 2. Psychometric Properties ---
    report.append("## 2. Psychometric Properties\n")
    matrix = np.array([[r[d] for d in DIMS] for r in rows])
    alpha = cronbachs_alpha(matrix)
    report.append(f"Cronbach's \u03b1 = {alpha:.3f}\n")

    corr = np.corrcoef(matrix.T)
    eigenvalues = np.sort(np.linalg.eigvalsh(corr))[::-1]
    total_var = eigenvalues.sum()
    var_explained = eigenvalues / total_var
    n_factors = sum(1 for ev in eigenvalues if ev > 1.0)
    report.append(
        f"Factor analysis: {n_factors} factor(s), "
        f"first explains {var_explained[0]*100:.0f}% of variance.\n"
    )

    # Full correlation matrix (7 dims)
    matrix7 = np.array([[r[d] for d in ALL_DIMS] for r in rows])
    corr7 = np.corrcoef(matrix7.T)
    report.append("Cross-correlation matrix:\n")
    report.append("| | " + " | ".join(ALL_DIMS) + " |")
    report.append("|---|" + "|".join(["---"] * len(ALL_DIMS)) + "|")
    for i, d in enumerate(ALL_DIMS):
        row_str = f"| **{d}** |"
        for j in range(len(ALL_DIMS)):
            row_str += f" {corr7[i, j]:.2f} |"
        report.append(row_str)
    report.append("")

    # --- 3. Criterion Validity ---
    report.append("## 3. Criterion Validity: Liked vs Disliked\n")
    liked = [r for r in rows if r["sample_group"] == "liked"]
    disliked = [r for r in rows if r["sample_group"] == "disliked"]
    neutral = [r for r in rows if r["sample_group"] == "neutral"]
    report.append(f"Liked: n={len(liked)}, Disliked: n={len(disliked)}, Neutral: n={len(neutral)}\n")

    report.append("| Dimension | Liked | Disliked | Neutral | \u0394(L-D) | d | 95% CI | p | sig |")
    report.append("|-----------|-------|----------|---------|------|---|--------|---|-----|")

    for d in ALL_DIMS + ["CQI"]:
        l_s = np.array([r[d] for r in liked])
        d_s = np.array([r[d] for r in disliked])
        n_s = np.array([r[d] for r in neutral])

        diff = np.mean(l_s) - np.mean(d_s)
        d_val = cohens_d(l_s, d_s)
        ci_lo, ci_hi = cohens_d_ci(d_val, len(l_s), len(d_s))
        u, p = stats.mannwhitneyu(l_s, d_s, alternative="two-sided")
        report.append(
            f"| {DIM_NAMES.get(d, d)} | {np.mean(l_s):.2f} | {np.mean(d_s):.2f} | "
            f"{np.mean(n_s):.2f} | {diff:+.2f} | {d_val:.2f} | "
            f"[{ci_lo:.2f}, {ci_hi:.2f}] | {p:.3f} | {sig_label(p)} |"
        )
    report.append("")

    # --- 4. Incremental Validity ---
    report.append("## 4. Incremental Validity: TC Alone vs Composites\n")
    ld = liked + disliked
    fb = np.array([1 if r["sample_group"] == "liked" else -1 for r in ld])
    scores = {d: np.array([r[d] for r in ld]) for d in ALL_DIMS}

    models = [
        ("TC alone", ["TC"]),
        ("TC + DF", ["TC", "DF"]),
        ("TC + FD", ["TC", "FD"]),
        ("TC + FD + TD", ["TC", "FD", "TD"]),
        ("Full CQI (6 dims)", DIMS),
        ("All 7 dimensions", ALL_DIMS),
    ]

    report.append("### Liked vs Disliked (n=%d)\n" % len(ld))
    report.append("| Model | Spearman \u03c1 | 95% CI | p | sig |")
    report.append("|-------|:---:|--------|:---:|:---:|")
    for name, dim_list in models:
        composite = np.mean([scores[d] for d in dim_list], axis=0)
        r, p = stats.spearmanr(composite, fb)
        z = np.arctanh(r)
        se = 1 / np.sqrt(len(ld) - 3)
        ci_lo = np.tanh(z - 1.96 * se)
        ci_hi = np.tanh(z + 1.96 * se)
        report.append(f"| {name} | {r:.3f} | [{ci_lo:.2f}, {ci_hi:.2f}] | {p:.3f} | {sig_label(p)} |")

    # Three-group
    all_fb = np.array([1 if r["sample_group"] == "liked" else (-1 if r["sample_group"] == "disliked" else 0) for r in rows])
    all_scores = {d: np.array([r[d] for r in rows]) for d in ALL_DIMS}
    report.append("\n### All three groups (n=%d)\n" % len(rows))
    report.append("| Model | Spearman \u03c1 | 95% CI | p | sig |")
    report.append("|-------|:---:|--------|:---:|:---:|")
    for name, dim_list in models:
        composite = np.mean([all_scores[d] for d in dim_list], axis=0)
        r, p = stats.spearmanr(composite, all_fb)
        z = np.arctanh(r)
        se = 1 / np.sqrt(len(rows) - 3)
        ci_lo = np.tanh(z - 1.96 * se)
        ci_hi = np.tanh(z + 1.96 * se)
        report.append(f"| {name} | {r:.3f} | [{ci_lo:.2f}, {ci_hi:.2f}] | {p:.3f} | {sig_label(p)} |")
    report.append("")

    # --- 5. Dark Factor Analysis ---
    report.append("## 5. Dark Factor Analysis\n")
    for group_name, group in [("Neutral", neutral), ("Liked", liked), ("Disliked", disliked)]:
        df_scores = [r["DF"] for r in group]
        n_concerning = sum(1 for s in df_scores if s <= 3)
        pct = n_concerning / len(df_scores) * 100
        n = len(df_scores)
        p_hat = n_concerning / n
        z = 1.96
        denom = 1 + z**2 / n
        center = (p_hat + z**2 / (2 * n)) / denom
        margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
        ci_lo = max(0, center - margin) * 100
        ci_hi = min(1, center + margin) * 100
        report.append(
            f"**{group_name}** (n={len(df_scores)}): "
            f"Mean DF={np.mean(df_scores):.2f}, "
            f"DF\u22643: {n_concerning} ({pct:.0f}%, 95% Wilson CI [{ci_lo:.0f}%, {ci_hi:.0f}%])"
        )
    report.append("")

    report.append("Pairwise comparisons (Mean DF):\n")
    for (name_a, group_a), (name_b, group_b) in [
        (("Neutral", neutral), ("Liked", liked)),
        (("Neutral", neutral), ("Disliked", disliked)),
        (("Liked", liked), ("Disliked", disliked)),
    ]:
        a = np.array([r["DF"] for r in group_a])
        b = np.array([r["DF"] for r in group_b])
        d_val = cohens_d(a, b)
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        report.append(f"- {name_a} vs {name_b}: d={d_val:.2f}, p={p:.3f} {sig_label(p)}")
    report.append("")

    return report


def main():
    parser = argparse.ArgumentParser(description="CQI Replication Analysis")
    parser.add_argument(
        "--data",
        default=os.path.join(os.path.dirname(__file__), "data", "cqi_scores.csv"),
        help="Path to CQI scores CSV file",
    )
    args = parser.parse_args()

    rows = load_csv(args.data)
    for line in analyze(rows):
        print(line)


if __name__ == "__main__":
    main()
