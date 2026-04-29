import os
from typing import List, Dict

import psycopg
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector


class PostgresStore:
    """Write embedded service snapshot rows back to Postgres inside a single transaction"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError(
                "DATABASE_URL environment variable is required.\n"
                "Add it to your .env file: DATABASE_URL=postgresql://user:password@host:port/dbname"
            )

    def write_all(self, rows: List[Dict], vectors: List[List[float]], batch_size: int) -> None:
        """
        Full run: TRUNCATE then INSERT all rows in a single transaction.
        Readers see old data until commit — no downtime window.
        """
        with psycopg.connect(self.connection_string) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {self.table_name}")
                for i in range(0, len(rows), batch_size):
                    self._insert_batch(cur, rows[i:i + batch_size], vectors[i:i + batch_size])
            conn.commit()

    def write_incremental(
        self,
        rows: List[Dict],
        vectors: List[List[float]],
        batch_size: int,
        deleted_service_ids: List[int],
    ) -> None:
        """
        Incremental run: delete stale snapshots for changed and soft-deleted services,
        then insert the fresh active rows.

        changed_service_ids — services that appear in rows (updated, still active)
        deleted_service_ids — services soft-deleted since last run (status != 1)
        """
        changed_service_ids = list({row['service_id'] for row in rows})
        to_delete = list(set(changed_service_ids) | set(deleted_service_ids))

        with psycopg.connect(self.connection_string) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                if to_delete:
                    cur.execute(
                        f"DELETE FROM {self.table_name} WHERE service_id = ANY(%s)",
                        (to_delete,),
                    )
                for i in range(0, len(rows), batch_size):
                    self._insert_batch(cur, rows[i:i + batch_size], vectors[i:i + batch_size])
            conn.commit()

    def _insert_batch(self, cur, rows: List[Dict], vectors: List[List[float]]) -> None:
        data = [
            (
                row['service_id'],
                row['resource_id'],
                row['address_id'],
                row['verified_at'],
                row['updated_at'],
                row['latitude'],
                row['longitude'],
                Jsonb(row['schedule']) if row['schedule'] is not None else None,
                row['category_ids'],
                row['category_names'],
                row['sfsg_category_ids'],
                row['sfsg_category_names'],
                row['eligibility_age'],
                row['eligibility_employment'],
                row['eligibility_ethnicity'],
                row['eligibility_family_status'],
                row['eligibility_financial'],
                row['eligibility_gender'],
                row['eligibility_health'],
                row['eligibility_immigration'],
                row['eligibility_housing'],
                row['eligibility_other'],
                row['eligibility_all'],
                row['embedding_text'],
                vector,
            )
            for row, vector in zip(rows, vectors)
        ]

        cur.executemany(
            f"""
            INSERT INTO {self.table_name} (
                service_id, resource_id, address_id,
                verified_at, updated_at, latitude, longitude, schedule,
                category_ids, category_names,
                sfsg_category_ids, sfsg_category_names,
                eligibility_age, eligibility_employment,
                eligibility_ethnicity, eligibility_family_status, eligibility_financial,
                eligibility_gender, eligibility_health, eligibility_immigration,
                eligibility_housing, eligibility_other, eligibility_all,
                embedding_text, embedding
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            """,
            data,
        )
