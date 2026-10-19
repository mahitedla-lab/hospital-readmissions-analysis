"""Load the CMS CSVs into DuckDB `raw` tables with normalised snake_case column names.

Every value is loaded as text; typing and cleaning happen in SQL (sql/01 and sql/02) so the
raw tables stay an exact copy of what CMS published.
"""
import re
from pathlib import Path

ALIASES = {
    "provider_number": "facility_id",
    "provider_id": "facility_id",
    "ccn": "facility_id",
    "hospital_name": "facility_name",
    "provider_name": "facility_name",
}

HRRP_REQUIRED = ["facility_id", "state", "measure_name", "excess_readmission_ratio"]
HRRP_OPTIONAL = [
    "facility_name", "number_of_discharges", "footnote", "predicted_readmission_rate",
    "expected_readmission_rate", "number_of_readmissions", "start_date", "end_date",
]
INFO_REQUIRED = ["facility_id", "state", "hospital_type", "hospital_ownership"]
INFO_OPTIONAL = ["facility_name"]


def normalize(column: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", column.strip().lower()).strip("_")
    return ALIASES.get(name, name)


def load_csv(con, csv_path, table: str, required: list[str], optional: list[str]) -> int:
    csv_path = Path(csv_path)
    path_sql = str(csv_path).replace("'", "''")
    reader = f"read_csv('{path_sql}', header=true, all_varchar=true)"

    original = [row[0] for row in con.execute(f"describe select * from {reader}").fetchall()]
    renamed = [normalize(c) for c in original]
    missing = [c for c in required if c not in renamed]
    if missing:
        raise ValueError(
            f"{csv_path.name}: expected column(s) {missing} but found {renamed}. "
            "CMS may have renamed a column; update ALIASES in readmissions/load.py."
        )

    select = [f'"{o}" as {n}' for o, n in zip(original, renamed)]
    select += [f"cast(null as varchar) as {c}" for c in optional if c not in renamed]

    con.execute("create schema if not exists raw")
    con.execute(f"create or replace table raw.{table} as select {', '.join(select)} from {reader}")
    return con.execute(f"select count(*) from raw.{table}").fetchone()[0]


def load_all(con, hrrp_csv, hospital_info_csv) -> dict[str, int]:
    return {
        "raw.hrrp": load_csv(con, hrrp_csv, "hrrp", HRRP_REQUIRED, HRRP_OPTIONAL),
        "raw.hospital_info": load_csv(con, hospital_info_csv, "hospital_info", INFO_REQUIRED, INFO_OPTIONAL),
    }
