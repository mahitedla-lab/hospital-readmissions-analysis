#!/usr/bin/env python3
"""End-to-end run: (download | synthetic | local CSVs) -> DuckDB -> SQL cleaning/merge -> tests -> CSV exports.

    python run_pipeline.py --download            # real CMS data (needs internet)
    python run_pipeline.py --hrrp a.csv --info b.csv
    python run_pipeline.py --synthetic           # offline smoke test, NOT real data
"""
import argparse
from pathlib import Path

from readmissions import common, download, export, hypothesis_tests, load, synthetic


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--download", action="store_true", help="download the current CMS files")
    src.add_argument("--synthetic", action="store_true", help="use generated synthetic data (not real)")
    src.add_argument("--hrrp", help="path to a local HRRP CSV (use with --info)")
    ap.add_argument("--info", help="path to a local Hospital General Information CSV")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--db", default="outputs/readmissions.duckdb")
    a = ap.parse_args()

    if a.download:
        paths = download.download_all(a.data_dir)
        hrrp, info = paths["hrrp.csv"], paths["hospital_general_information.csv"]
    elif a.synthetic:
        print("*** SYNTHETIC DATA: results are for testing the code only ***")
        hrrp, info = synthetic.make_synthetic(Path(a.data_dir) / "synthetic")
    else:
        if not a.info:
            ap.error("--hrrp requires --info")
        hrrp, info = a.hrrp, a.info

    con = common.connect(a.db)
    print("loaded:", load.load_all(con, hrrp, info))
    print("sql:", ", ".join(common.run_sql_files(con)))
    out = Path(a.out_dir)
    tests, ols = hypothesis_tests.run_all(con)
    out.mkdir(parents=True, exist_ok=True)
    tests.to_csv(out / "hypothesis_tests.csv", index=False)
    ols.to_csv(out / "ols_ownership_size.csv", index=False)
    export.export_tables(con, out / "tableau")
    print(con.execute("select check_name, value from analysis.data_checks").df().to_string(index=False))
    print(tests[tests.test.str.startswith(("Kruskal", "Chi"))][["test", "p_value", "effect_size", "effect_name"]].to_string(index=False))
    print(f"outputs written to {out}/")


if __name__ == "__main__":
    main()
