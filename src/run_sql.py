from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# OLIST E-COMMERCE ANALYTICS
# SQL QUERY RUNNER
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "database" / "olist_analytics.db"
SQL_PATH = BASE_DIR / "sql" / "analytical_queries.sql"


def run_queries():

    print("\n" + "=" * 70)
    print("OLIST E-COMMERCE SQL ANALYTICS")
    print("=" * 70)

    # Check database
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    # Check SQL file
    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"SQL file not found:\n{SQL_PATH}"
        )

    print(f"\nDatabase:")
    print(DB_PATH)

    print(f"\nSQL file:")
    print(SQL_PATH)

    # Connect database
    conn = sqlite3.connect(DB_PATH)

    # Read SQL file
    sql_text = SQL_PATH.read_text(
        encoding="utf-8"
    )

    # Split queries using semicolon
    queries = [
        query.strip()
        for query in sql_text.split(";")
        if query.strip()
    ]

    print(
        f"\nTotal SQL queries found: {len(queries)}"
    )

    print("\n" + "-" * 70)

    # Execute every query
    for number, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"\nQUERY {number}"
        )

        print("-" * 70)

        try:

            df = pd.read_sql_query(
                query,
                conn
            )

            if df.empty:

                print(
                    "No rows returned."
                )

            else:

                print(
                    df.to_string(
                        index=False
                    )
                )

        except Exception as error:

            print(
                f"ERROR in Query {number}:"
            )

            print(error)

    conn.close()

    print("\n" + "=" * 70)
    print("SQL ANALYSIS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_queries()