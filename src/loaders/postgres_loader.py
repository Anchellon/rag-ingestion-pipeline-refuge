import os
from typing import List, Dict
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


class PostgresLoader:
    """Load service snapshot rows from Postgres by executing the denormalization SQL"""

    def __init__(self, sql_file: str):
        self.sql_file = sql_file
        self.connection_string = self._build_connection_string()

    @staticmethod
    def _build_connection_string() -> str:
        # Accept either a full URL or individual components (as injected by ECS secrets)
        url = os.getenv('DATABASE_URL')
        if url:
            return url
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT', '5432')
        name = os.getenv('DB_NAME', 'shelter')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        if not all([host, user, password]):
            raise ValueError(
                "Set DATABASE_URL or all of DB_HOST, DB_USER, DB_PASSWORD."
            )
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    def load(self, last_run_at: str = "never") -> List[Dict]:
        """
        Execute the denormalization SQL and return active (status=1) rows.

        For a full run (last_run_at="never"), returns all rows.
        For an incremental run, wraps the SQL and filters by updated_at > last_run_at
        so only changed rows are returned (re-embedded and re-inserted).
        """
        sql_path = Path(self.sql_file)
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_file}")

        with open(sql_path, 'r') as f:
            base_sql = f.read()

        if last_run_at == "never":
            sql = base_sql
            params = None
        else:
            sql = f"SELECT * FROM ({base_sql}) AS snapshot WHERE updated_at > %s"
            params = (last_run_at,)

        with psycopg.connect(self.connection_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        return rows

    def load_deleted_ids(self, last_run_at: str) -> List[int]:
        """
        Return service IDs that were soft-deleted (status != 1) since last_run_at.
        These snapshots should be removed from service_snapshots.
        """
        with psycopg.connect(self.connection_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM services WHERE status != 1 AND updated_at > %s",
                    (last_run_at,),
                )
                rows = cur.fetchall()

        return [row['id'] for row in rows]
