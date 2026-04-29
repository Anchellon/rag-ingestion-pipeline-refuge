# Service Snapshot Ingestion Pipeline

Denormalizes service data from PostgreSQL, generates embeddings, and writes them back to a `service_snapshots` table with pgvector for semantic search.

> PDF ingestion pipeline is maintained on the `pdf-pipeline` branch.

## How it works

```
PostgreSQL (source tables)
  → Denormalization SQL  →  prose embedding_text per service
  → Embedding model      →  768-dim vectors
  → service_snapshots    →  TRUNCATE + INSERT (atomic, no downtime)
```

The denormalization SQL (`sql/service_snapshot.sql`) handles all the heavy lifting — joining services, resources, programs, addresses, schedules, eligibility, and categories into a single prose string per service. The Python pipeline reads those rows, embeds them, and writes everything back in one transaction.

## Project structure

```
ingestion-pipeline/
├── src/
│   ├── loaders/
│   │   └── postgres_loader.py       # Executes denormalization SQL, returns rows
│   ├── embeddings/
│   │   └── embedder.py              # Provider-agnostic embedding wrapper
│   ├── storage/
│   │   └── postgres_store.py        # TRUNCATE + INSERT into service_snapshots
│   ├── pipeline/
│   │   └── postgres_ingestion.py    # Orchestrates load → embed → write
│   └── utils/
│       └── config.py                # Loads config.yaml + .env overrides
├── sql/
│   ├── service_snapshot.sql         # Denormalization query (read)
│   └── create_service_snapshot.sql  # DDL for service_snapshots table (run once)
├── scripts/
│   └── ingest_postgres.py           # Entry point
├── tests/
│   ├── conftest.py
│   └── test_metadata_serialization.py
├── config/
│   └── config.yaml
└── .env.example
```

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- An embedding provider (Ollama by default — swap via config)

### Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Required in `.env`:
```bash
DATABASE_URL=postgresql://user:password@host:port/dbname
OLLAMA_BASE_URL=http://localhost:11434
```

The embedding provider, model, and all other settings are in `config/config.yaml`. Environment variables take precedence over the config file.

### Create the target table (first time only)

```bash
psql $DATABASE_URL -f sql/create_service_snapshot.sql
```

### Run

```bash
python scripts/ingest_postgres.py
```

## Configuration

`config/config.yaml`:

```yaml
embeddings:
  provider: "ollama"        # swap to "bedrock" or "openai" without code changes
  model: "nomic-embed-text"
  base_url: "http://localhost:11434"

postgres:
  table_name: "service_snapshots"
  sql_file: "sql/service_snapshot.sql"
  batch_size: 100
```

## Embedding providers

The `provider` field in `config.yaml` controls which embedding backend is used. Swapping providers requires no code changes — only config:

| Provider | `provider` value | Notes |
|----------|-----------------|-------|
| Ollama (local) | `ollama` | Default, requires Ollama running |
| Amazon Bedrock | `bedrock` | For AWS deployments |
| OpenAI | `openai` | Requires `OPENAI_API_KEY` |

## Testing

```bash
pytest
pytest -v
pytest --cov=src
```

## Deployment (AWS)

Intended deployment: **EventBridge cron → ECS Fargate task**.

- Swap embedding provider to `bedrock` in config
- `DATABASE_URL` stored in Secrets Manager, injected at runtime via IAM role
- Nightly schedule keeps `service_snapshots` fresh without event-driven complexity
