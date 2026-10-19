"""Write the analysis tables to CSV (one file per table) for Tableau."""
from pathlib import Path

TABLES = [
    "analysis.hospital_condition", "analysis.hospital_summary", "analysis.condition_summary",
    "analysis.state_condition_summary", "analysis.state_summary", "analysis.condition_ownership_summary",
    "analysis.segment_risk", "analysis.data_checks",
]


def export_tables(con, out_dir) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for table in TABLES:
        dest = out_dir / f"{table.split('.')[1]}.csv"
        con.execute(f"copy (select * from {table}) to '{dest}' (header, delimiter ',')")
        paths.append(dest)
    return paths
