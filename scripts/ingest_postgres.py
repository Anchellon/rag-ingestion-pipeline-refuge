import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.pipeline.postgres_ingestion import PostgresIngestionPipeline


def main():
    print("\nLoading configuration...")
    config = load_config('config/config.yaml')
    print("✓ Configuration loaded")

    pipeline = PostgresIngestionPipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()
