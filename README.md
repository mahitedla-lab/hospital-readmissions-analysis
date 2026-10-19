# Hospital Readmissions Performance Analysis

Merges the CMS **Hospital Readmissions Reduction Program (HRRP)** data for 3,000+ hospitals with **Hospital General Information** in SQL, compares **excess readmission ratios (ERR)** across the **6 HRRP conditions** (AMI, CABG, COPD, heart failure, hip/knee arthroplasty, pneumonia) and **all states**, runs **hypothesis tests by ownership type and hospital size**, and feeds a **Tableau** dashboard that highlights the segments carrying the highest readmission-penalty risk. ERR > 1 means more readmissions than expected for a hospital's case mix, which exposes it to an HRRP payment penalty.

```
CMS CSVs -> DuckDB raw -> sql/01-02 clean -> sql/03 merge (hospital x condition) -> sql/04 hospital summary
   -> sql/05 summaries -> hypothesis tests (scipy/statsmodels) -> CSV exports -> Tableau
```

## What is verified, and what is not
- **Verified:** the pipeline and statistics run end to end on *synthetic* CMS-shaped data (`pytest`, also in GitHub Actions). Tests check zero-padded ID joins, suppressed-value handling, the one-row-per-hospital-condition grain, size tiers, and that the hypothesis tests detect effects planted in the synthetic data.
- **Not run here:** the real CMS download (the build environment could not reach data.cms.gov), so this repo contains **no real findings or counts**. Run it on real data with the command below; results land in `outputs/`.
- The Tableau workbook is binary; `tableau/DASHBOARD_SPEC.md` gives the sheets and calculated fields.

## Method notes
- **Join key:** `Facility ID`, zero-padded to 6 characters. HRRP is the left side, so hospitals with no General Information match are kept with ownership `Unknown` (counted in `analysis.data_checks`).
- **Suppression:** CMS values such as "N/A" / "Too Few to Report" become NULL and those rows are excluded, never treated as zero.
- **Hospital size:** General Information has no bed count, so size = tercile (Small/Medium/Large) of total HRRP-measured discharges per hospital. This measures HRRP volume, not licensed beds.
- **Ownership:** CMS's 10+ labels are grouped into Government / Non-profit / For-profit / Other.
- **Tests (alpha 0.05):** Kruskal-Wallis on hospital mean ERR (ERR is not normal) with epsilon-squared; pairwise Mann-Whitney with Holm correction; chi-square (Cramer's V) on penalty exposure; two-way OLS with robust errors for ownership and size together. Effect sizes are reported beside p-values because large samples make tiny gaps "significant".

## Run it
```bash
pip install -r requirements.txt
python run_pipeline.py --download     # real CMS data; or --hrrp X.csv --info Y.csv
python -m pytest -q tests             # synthetic-data checks
python run_pipeline.py --synthetic    # offline smoke test (not real data)
```
Outputs: `outputs/hypothesis_tests.csv`, `outputs/ols_ownership_size.csv`, `outputs/tableau/*.csv`, DuckDB file `outputs/readmissions.duckdb` (all git-ignored).
