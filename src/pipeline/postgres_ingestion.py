import os
from datetime import datetime, timezone
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
            base_url=config['embeddings'].get('base_url', ''),
        )

        self.store = PostgresStore(table_name=pg['table_name'])
        self.batch_size = pg['batch_size']

        print("✓ Pipeline initialized")

    # ------------------------------------------------------------------
    # SSM helpers — gracefully degrade when running outside ECS/AWS
    # ------------------------------------------------------------------

    def _read_last_run_at(self) -> str:
        ssm_param = os.getenv('SSM_LAST_RUN_PARAM')
        if not ssm_param:
            return "never"
        try:
            import boto3
            ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            response = ssm.get_parameter(Name=ssm_param)
            return response['Parameter']['Value']
        except Exception as e:
            print(f"  ⚠ Could not read SSM param ({e}) — defaulting to full run")
            return "never"

    def _write_last_run_at(self, timestamp: str) -> None:
        ssm_param = os.getenv('SSM_LAST_RUN_PARAM')
        if not ssm_param:
            return
        try:
            import boto3
            ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            ssm.put_parameter(Name=ssm_param, Value=timestamp, Type='String', Overwrite=True)
            print(f"  ✓ SSM last_run_at updated → {timestamp}")
        except Exception as e:
            print(f"  ⚠ Could not write SSM param: {e}")

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self) -> Dict:
        print(f"\n{'='*60}")
        print("POSTGRES INGESTION PIPELINE")
        print(f"{'='*60}")

        last_run_at = self._read_last_run_at()
        is_full_run = (last_run_at == "never")
        run_mode = "FULL" if is_full_run else f"INCREMENTAL (since {last_run_at})"
        print(f"\nMode: {run_mode}")

        # Step 1: Load
        print("\n[1/3] Loading rows from database...")
        rows = self.loader.load(last_run_at=last_run_at)
        total = len(rows)
        print(f"  ✓ Loaded {total} rows")

        deleted_service_ids: List[int] = []
        if not is_full_run:
            deleted_service_ids = self.loader.load_deleted_ids(last_run_at=last_run_at)
            if deleted_service_ids:
                print(f"  ✓ {len(deleted_service_ids)} soft-deleted service(s) to remove")

        if not rows and not deleted_service_ids:
            print("  — No changes since last run, nothing to do")
            return {
                'total_rows': 0,
                'total_batches': 0,
                'table': self.config['postgres']['table_name'],
                'status': 'skipped',
            }

        # Step 2: Embed
        batches = [rows[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        total_batches = len(batches)
        all_vectors: List[List[float]] = []

        if rows:
            expected_dim = self.config['embeddings'].get('embedding_dimension')
            print(f"\n[2/3] Embedding {total} rows in {total_batches} batches of {self.batch_size}...")

            for i, batch in enumerate(batches, start=1):
                texts = [row['embedding_text'] for row in batch]
                vectors = self.embedder.embed_documents(texts)

                if i == 1 and expected_dim is not None:
                    actual_dim = len(vectors[0])
                    if actual_dim != expected_dim:
                        raise ValueError(
                            f"Embedding dimension mismatch: model produced {actual_dim}d vectors "
                            f"but config expects {expected_dim}d. "
                            f"Update embedding_dimension in config.yaml AND re-run the DDL migration."
                        )

                all_vectors.extend(vectors)
                print(f"  Batch {i}/{total_batches} — {len(batch)} rows embedded")
        else:
            print("\n[2/3] No active rows to embed — skipping embedding step")

        # Step 3: Write
        print(f"\n[3/3] Writing to {self.config['postgres']['table_name']}...")
        if is_full_run:
            self.store.write_all(rows, all_vectors, self.batch_size)
        else:
            self.store.write_incremental(rows, all_vectors, self.batch_size, deleted_service_ids)
        print(f"  ✓ {total} rows written")

        # Update SSM timestamp
        self._write_last_run_at(datetime.now(timezone.utc).isoformat())

        print(f"\n{'='*60}")
        print("✓ Ingestion complete")
        print(f"  Mode:    {run_mode}")
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
