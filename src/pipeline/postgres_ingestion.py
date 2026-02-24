from typing import Dict, List

from ..loaders.postgres_loader import PostgresLoader
from ..embeddings.embedder import Embedder
from ..storage.postgres_store import PostgresStore


class PostgresIngestionPipeline:
    """Pipeline for embedding service snapshots and writing them to Postgres"""

    def __init__(self, config: dict):
        self.config = config
        pg = config['postgres']

        print("Initializing Postgres ingestion pipeline...")

        self.loader = PostgresLoader(sql_file=pg['sql_file'])

        self.embedder = Embedder(
            provider=config['embeddings']['provider'],
            model=config['embeddings']['model'],
            base_url=config['embeddings']['base_url'],
        )

        self.store = PostgresStore(table_name=pg['table_name'])

        self.batch_size = pg['batch_size']

        print("✓ Pipeline initialized")

    def run(self) -> Dict:
        """
        Execute the full ingestion:
          1. Load all rows from Postgres via the denormalization SQL
          2. Embed all rows in batches (outside the DB transaction)
          3. TRUNCATE + INSERT everything in a single transaction

        Returns:
            Summary dict with total_rows, total_batches, table, status
        """
        print(f"\n{'='*60}")
        print("POSTGRES INGESTION PIPELINE")
        print(f"{'='*60}")

        # Step 1: Load
        print("\n[1/3] Loading rows from database...")
        rows = self.loader.load()
        total = len(rows)
        print(f"  ✓ Loaded {total} rows")

        if not rows:
            print("  ✗ No rows returned from SQL — nothing to ingest")
            return {
                'total_rows': 0,
                'total_batches': 0,
                'table': self.config['postgres']['table_name'],
                'status': 'skipped',
            }

        # Step 2: Embed (all batches, before opening the DB transaction)
        batches = [rows[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        total_batches = len(batches)

        print(f"\n[2/3] Embedding {total} rows in {total_batches} batches of {self.batch_size}...")
        all_vectors: List[List[float]] = []

        for i, batch in enumerate(batches, start=1):
            texts = [row['embedding_text'] for row in batch]
            vectors = self.embedder.embed_documents(texts)
            all_vectors.extend(vectors)
            print(f"  Batch {i}/{total_batches} — {len(batch)} rows embedded")

        # Step 3: Write (single transaction — TRUNCATE then INSERT)
        print(f"\n[3/3] Writing to {self.config['postgres']['table_name']}...")
        self.store.write_all(rows, all_vectors, self.batch_size)
        print(f"  ✓ {total} rows written")

        print(f"\n{'='*60}")
        print("✓ Ingestion complete")
        print(f"  Rows:    {total}")
        print(f"  Batches: {total_batches}")
        print(f"  Table:   {self.config['postgres']['table_name']}")
        print(f"{'='*60}\n")

        return {
            'total_rows': total,
            'total_batches': total_batches,
            'table': self.config['postgres']['table_name'],
            'status': 'success',
        }
