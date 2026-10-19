from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"


def connect(db_path) -> duckdb.DuckDBPyConnection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def run_sql_files(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Execute every sql/NN_*.sql script in order. Returns the file names that ran."""
    ran = []
    for path in sorted(SQL_DIR.glob("*.sql")):
        con.execute(path.read_text())
        ran.append(path.name)
    return ran
