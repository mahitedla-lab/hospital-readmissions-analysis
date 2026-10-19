# Tableau dashboard build guide

A `.twbx` workbook is binary and must be authored in Tableau, so this guide lists the data sources, calculated fields and sheets. Run `python run_pipeline.py --download` first; the CSVs in `outputs/tableau/` are the data sources (Tableau Public works).

## Data sources
| File | Grain | Use |
|---|---|---|
| `hospital_condition.csv` | hospital x condition | detail, distributions |
| `hospital_summary.csv` | hospital | ownership / size segments |
| `state_condition_summary.csv` | state x condition | map and heatmap |
| `condition_summary.csv` | condition | nationwide comparison |
| `segment_risk.csv` | ownership / size / ownership x size | penalty-risk ranking |

## Calculated fields
```
Above 1 (flag)        IF [Excess Readmission Ratio] > 1 THEN 1 ELSE 0 END
Pct Above 1           AVG([Err Above 1])            // share of hospital results with ERR > 1
ERR Band              IF [Excess Readmission Ratio] > 1.05 THEN "High (>1.05)"
                      ELSEIF [Excess Readmission Ratio] > 1 THEN "Penalty exposure (1-1.05)"
                      ELSE "At or below expected" END
```
Format `pct_*` columns as percentages; diverge colors at ERR = 1.

## Sheets
1. **State x condition heatmap**: rows `state`, columns `condition`, color `mean_err` (diverging at 1.0). Filter: condition.
2. **State map**: filled map by `state`, color `mean_hospital_err` from `state_summary.csv`.
3. **Condition comparison**: bars of `mean_err` and `pct_above_1` by `condition`, with a reference line at 1.0.
4. **Ownership box plot**: `ownership_group` vs `excess_readmission_ratio` (from `hospital_condition.csv`), split by condition.
5. **Segment penalty risk**: bars of `pct_hospitals_exposed` by `segment`, sorted by `risk_rank`, one panel each for Ownership, Size, Ownership x Size. Pair with the hypothesis-test results in `outputs/hypothesis_tests.csv` (p-value and effect size) in a text box.

Size = tercile of total HRRP discharges (CMS General Information has no bed count).
