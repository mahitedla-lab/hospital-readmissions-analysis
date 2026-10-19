"""Hypothesis tests on hospital-level excess readmission ratios (ERR).

Outcome: mean ERR per hospital (analysis.hospital_summary.mean_err) and penalty exposure
(ERR > 1 on at least one condition). Groups: ownership_group and size_tier (discharge terciles).

Tests (alpha = 0.05):
  * Kruskal-Wallis (non-parametric; ERR is not normal) with epsilon-squared effect size
  * Pairwise Mann-Whitney U with Holm correction, rank-biserial effect size
  * Chi-square test of independence on penalty exposure, with Cramer's V
  * Two-way OLS (ownership + size) with HC3 robust errors: do the gaps persist after controlling
    for each other?
Statistical significance with thousands of hospitals can be tiny in practice, so effect sizes
are always reported next to p-values.
"""
from itertools import combinations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05


def load_hospitals(con) -> pd.DataFrame:
    df = con.execute(
        "select * from analysis.hospital_summary where size_tier <> 'Unknown' and mean_err is not null"
    ).df()
    return df


def kruskal(df: pd.DataFrame, group: str, value: str = "mean_err") -> dict:
    groups = [g[value].to_numpy() for _, g in df.groupby(group) if len(g) >= 5]
    n, k = sum(len(g) for g in groups), len(groups)
    h, p = stats.kruskal(*groups)
    return {"test": f"Kruskal-Wallis: {value} by {group}", "statistic": h, "p_value": p, "groups": k, "n": n,
            "effect_size": (h - k + 1) / (n - k), "effect_name": "epsilon-squared"}


def pairwise(df: pd.DataFrame, group: str, value: str = "mean_err") -> list[dict]:
    levels = [lv for lv, g in df.groupby(group) if len(g) >= 5]
    raw = []
    for a, b in combinations(levels, 2):
        x, y = df.loc[df[group] == a, value], df.loc[df[group] == b, value]
        u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
        raw.append({"test": f"Mann-Whitney: {a} vs {b} ({value})", "statistic": u, "p_value": p,
                    "n": len(x) + len(y), "median_a": x.median(), "median_b": y.median(),
                    "effect_size": 2 * u / (len(x) * len(y)) - 1, "effect_name": "rank-biserial (a vs b)"})
    if raw:
        adj = multipletests([r["p_value"] for r in raw], method="holm")[1]
        for r, pa in zip(raw, adj):
            r["p_adjusted"] = pa
    return raw


def exposure_chi2(df: pd.DataFrame, group: str) -> dict:
    table = pd.crosstab(df[group], df["has_penalty_exposure"])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    n = table.to_numpy().sum()
    v = np.sqrt(chi2 / (n * (min(table.shape) - 1)))
    return {"test": f"Chi-square: penalty exposure by {group}", "statistic": chi2, "p_value": p, "n": int(n),
            "groups": table.shape[0], "effect_size": v, "effect_name": "Cramer's V"}


def two_way_ols(df: pd.DataFrame) -> pd.DataFrame:
    fit = smf.ols("mean_err ~ C(ownership_group, Treatment('Non-profit')) + C(size_tier, Treatment('Large'))",
                  data=df).fit(cov_type="HC3")
    out = pd.DataFrame({"term": fit.params.index, "coef": fit.params.values, "p_value": fit.pvalues.values,
                        "ci_low": fit.conf_int()[0].values, "ci_high": fit.conf_int()[1].values})
    out["test"] = "OLS mean_err ~ ownership + size (HC3)"
    out["n"] = int(fit.nobs)
    return out


def run_all(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = load_hospitals(con)
    rows = []
    for g in ("ownership_group", "size_tier"):
        rows.append(kruskal(df, g))
        rows.extend(pairwise(df, g))
        rows.append(exposure_chi2(df, g))
    tests = pd.DataFrame(rows)
    tests["significant_at_0.05"] = tests.get("p_adjusted", tests["p_value"]).fillna(tests["p_value"]) < ALPHA
    return tests, two_way_ols(df)
