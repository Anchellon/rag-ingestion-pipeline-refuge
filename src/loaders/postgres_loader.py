import os
from typing import List, Dict
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


class PostgresLoader:
    """Load service snapshot rows from Postgres by executing the denormalization SQL"""

    def __init__(self, sql_file: str):
        self.sql_file = sql_file
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError(
                "DATABASE_URL environment variable is required.\n"
                "Add it to your .env file: DATABASE_URL=postgresql://user:password@host:port/dbname"
            )

    def load(self) -> List[Dict]:
        """
        Execute the denormalization SQL and return all rows as dicts.

        Returns:
            List of dicts, one per service-location combination.
            Each dict contains all columns including embedding_text.
        """
        sql_path = Path(self.sql_file)
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_file}")

        with open(sql_path, 'r') as f:
            sql = f.read()

        with psycopg.connect(self.connection_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()

        return rows
