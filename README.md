# PDF Ingestion Pipeline with LLM-Powered Metadata Extraction

A production-ready ingestion pipeline for processing PDF documents, extracting structured metadata using local LLMs, and storing them in a vector database for semantic search.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This pipeline transforms PDF documents into searchable, semantically-enriched data by:

1. **📄 Loading PDFs** - Extracts text content while preserving metadata
2. **✂️ Smart Chunking** - Splits documents intelligently with configurable overlap
3. **🤖 LLM Extraction** - Automatically extracts structured metadata (service info, location, contact details)
4. **🔢 Embedding Generation** - Creates vector embeddings for semantic search
5. **💾 Vector Storage** - Stores in ChromaDB with rich, queryable metadata

**Perfect for**: Service directories, knowledge bases, RAG systems, document search applications

## ✨ Key Features

- 🏠 **100% Local** - Uses Ollama (no external API calls, complete data privacy)
- 🤖 **Smart Extraction** - LLM extracts service type, location, contact info, hours automatically
- 🎯 **Rich Metadata** - Structured Pydantic models with validation
- 🔍 **Semantic Search** - Vector embeddings for intelligent document retrieval
- ⚙️ **Highly Configurable** - YAML config + environment variable overrides
- ✅ **Production Ready** - Comprehensive test suite, type hints, error handling
- 🚀 **Cross-Platform** - Works on Windows, Mac, Linux, WSL, Docker

## 📋 Use Cases

- **Service Directories**: Ingest brochures for food banks, housing services, healthcare providers
- **Knowledge Bases**: Process documentation, guides, policies for Q&A systems
- **Document Search**: Build semantic search across large document collections
- **RAG Applications**: Foundation for AI-powered question answering

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai) installed and running

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ingestion-pipeline

# 2. Create and activate virtual environment
python -m venv .venv

# On Linux/Mac/WSL:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull required Ollama models
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Configuration

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and set your Ollama URL
# For most systems (Mac/Linux/Windows):
OLLAMA_BASE_URL=http://localhost:11434

# For WSL users, find your WSL IP:
# ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
# Then set:
OLLAMA_BASE_URL=http://<your-wsl-ip>:11434
```

### Run Your First Ingestion

```bash
# Process the sample PDF
python scripts/ingest.py
```

**Expected Output:**
```
============================================================
PDF INGESTION PIPELINE
============================================================

✓ Loaded 2 pages
✓ Created 4 chunks
✓ Extracted metadata
  - Service Type: food
  - City: San Francisco
✓ Stored in ChromaDB

✓ All done!
```

## ⚙️ Configuration

### Environment Variables (.env)

**Required:**
```bash
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
```

**Optional Overrides** (defaults in `config/config.yaml`):
```bash
OLLAMA_LLM_MODEL=llama3.2              # LLM for extraction
OLLAMA_EMBEDDING_MODEL=nomic-embed-text # Embedding model
CHROMA_PERSIST_DIR=./chroma_db         # Database directory
CHROMA_COLLECTION_NAME=pdf-documents   # Collection name
CHUNK_SIZE=512                         # Chunk size in tokens
CHUNK_OVERLAP=50                       # Overlap between chunks
```

### Application Config (config/config.yaml)

```yaml
chunking:
  chunk_size: 512    # Default chunk size
  overlap: 50        # Overlap for context preservation

metadata:
  use_llm: true
  provider: "ollama"
  llm_model: "llama3.2"

embeddings:
  provider: "ollama"
  model: "nomic-embed-text"

vectorstore:
  provider: "chroma"
  params:
    persist_directory: "./chroma_db"
    collection_name: "pdf-documents"
```

**Priority**: `.env` variables override `config.yaml` defaults

## 📁 Project Structure

```
ingestion-pipeline/
├── src/
│   ├── loaders/              # PDF loading
│   │   └── pdf_loader.py
│   ├── metadata/             # Metadata extraction & schemas
│   │   ├── schema.py         # Pydantic models
│   │   └── llm_extractor.py  # LLM-powered extraction
│   ├── embeddings/           # Vector embeddings
│   │   └── embedder.py
│   ├── storage/              # Vector database
│   │   └── vectorstore.py
│   ├── pipeline/             # Main pipeline
│   │   └── ingestion.py
│   └── utils/
│       ├── config.py         # Config loader
│       └── metadata_serializer.py  # ChromaDB compatibility
│
├── tests/                    # Pytest test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_metadata_serialization.py
│   ├── test_llm_extraction.py
│   └── test_pipeline.py
│
├── scripts/
│   └── ingest.py             # Main ingestion script
│
├── config/
│   └── config.yaml           # Application config
│
├── .env.example              # Environment template
├── requirements.txt          # Dependencies
├── pytest.ini                # Test configuration
└── README.md                 # This file
```

## 🔄 How It Works

### 1. PDF Loading
```python
from src.loaders.pdf_loader import PDFLoader

loader = PDFLoader()
documents = loader.load("path/to/document.pdf")
# Returns: List[Document] with text and metadata
```

### 2. Text Chunking
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)
```

### 3. Metadata Extraction (LLM-Powered)
```python
from src.metadata.llm_extractor import LLMMetadataExtractor

extractor = LLMMetadataExtractor(model="llama3.2")
metadata = extractor.extract(chunk.page_content)

# Returns structured metadata:
{
    "service_type": "food",
    "city": "San Francisco",
    "contact": {"phone": "(415) 555-1234", "email": "info@..."},
    "location": {"address": "123 Main St", "city": "SF", "state": "CA"},
    "service_details": {"hours": {...}, "eligibility": "All welcome"},
    "mentioned_services": ["Soup Kitchen", "Food Bank"],
    "mentioned_organizations": ["Fraternite Notre Dame"]
}
```

### 4. Embedding & Storage
```python
from src.embeddings.embedder import Embedder
from src.storage.vectorstore import VectorStore

embedder = Embedder(model="nomic-embed-text")
vectorstore = VectorStore(embeddings=embedder.embeddings)

# Store with flattened, ChromaDB-compatible metadata
vectorstore.add_documents(enriched_chunks)
```

### 5. Querying (Example)
```python
# Semantic search with metadata filters
results = vectorstore.similarity_search(
    query="food banks in San Francisco",
    k=5,
    filter={
        "extracted_service_type": "food",
        "extracted_city": "San Francisco"
    }
)
```

## 🧪 Testing

Comprehensive pytest test suite with 14+ tests.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests (fast, no LLM)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_llm_extraction.py
```

**Test Coverage:**
- ✅ Metadata serialization (ChromaDB compatibility)
- ✅ LLM extraction (response format, data extraction)
- ✅ Full pipeline (PDF loading, chunking, storage)
- ✅ Error handling

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 📊 Metadata Schema

The pipeline extracts rich, structured metadata validated with Pydantic:

```python
{
    # Core Classification
    "service_type": "food",           # food, housing, healthcare, etc.
    "city": "San Francisco",
    "neighborhood": "Mission District",

    # Organizations & Services
    "mentioned_services": ["Soup Kitchen", "Food Bank"],
    "mentioned_organizations": ["Fraternite Notre Dame"],

    # Contact Information
    "contact": {
        "phone": "(415) 555-1234",
        "email": "info@example.com",
        "website": "https://example.com"
    },

    # Location Details
    "location": {
        "address": "123 Main Street",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94103"
    },

    # Service Details
    "service_details": {
        "hours": {"monday": "9am-5pm"},
        "eligibility": "All welcome",
        "cost": "Free",
        "languages": ["English", "Spanish"]
    }
}
```

**Automatic Processing:**
- ✅ Flattened for ChromaDB (nested → `extracted_contact_phone`)
- ✅ Validated with Pydantic schemas
- ✅ Serialized to primitives only (str, int, float, bool)
- ✅ None values removed (ChromaDB requirement)

## 🔧 Advanced Usage

### Custom PDF Processing

```python
from src.pipeline.ingestion import IngestionPipeline
from src.utils.config import load_config

config = load_config()
pipeline = IngestionPipeline(config)

result = pipeline.process_pdf("path/to/your.pdf")

print(f"Processed {result['pages']} pages")
print(f"Created {result['chunks']} chunks")
print(f"Service: {result['service_type']}")
print(f"City: {result['city']}")
```

### Batch Processing

```python
from pathlib import Path

pdf_dir = Path("data/pdfs")
for pdf_file in pdf_dir.glob("*.pdf"):
    result = pipeline.process_pdf(str(pdf_file))
    print(f"✓ {pdf_file.name}: {result['chunks']} chunks")
```

### Custom Metadata Extraction

```python
from src.metadata.llm_extractor import LLMMetadataExtractor

extractor = LLMMetadataExtractor(
    model="llama3.2",           # Or llama3.1, mistral, etc.
    base_url="http://localhost:11434"
)

text = "Your document text here..."
metadata = extractor.extract(text)
```

## 🐛 Troubleshooting

### LLM Extraction Returns None

**Symptoms**: All metadata fields are None

**Solutions**:
```bash
# 1. Check Ollama is running
curl $OLLAMA_BASE_URL/api/tags

# 2. Verify model is available
ollama list

# 3. Check .env file exists and has correct URL
cat .env

# 4. Test extraction manually
pytest tests/test_llm_extraction.py::TestLLMExtraction::test_basic_extraction -s
```

### ImportError or ModuleNotFoundError

**Solution**:
```bash
# Ensure virtual environment is activated
which python  # Should show .venv path

# Reinstall dependencies
pip install -r requirements.txt
```

### ChromaDB Errors

**Solution**:
```bash
# Clear and rebuild database
rm -rf chroma_db/
python scripts/ingest.py
```

### "OLLAMA_BASE_URL environment variable is required"

**Solution**:
```bash
# Create .env file from template
cp .env.example .env

# Edit .env and set your Ollama URL
# For most systems:
echo "OLLAMA_BASE_URL=http://localhost:11434" > .env
```

### WSL Users: Cannot connect to Ollama

**Solution**:
```bash
# Find your WSL IP
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'

# Set in .env
echo "OLLAMA_BASE_URL=http://<your-wsl-ip>:11434" > .env
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone <your-repo-url>
cd ingestion-pipeline
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v

# Run with coverage
pytest --cov=src
```

## 📚 Documentation

- [Testing Guide](tests/README.md) - Comprehensive testing documentation
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [LangChain Documentation](https://python.langchain.com)
- [Pydantic Documentation](https://docs.pydantic.dev)

## 🔐 Security & Privacy

- ✅ **100% Local Processing** - All data stays on your machine
- ✅ **No External API Calls** - Uses local Ollama models
- ✅ **Secure Configuration** - `.env` files excluded from git
- ✅ **Database Protection** - ChromaDB data not committed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM inference
- [LangChain](https://langchain.com) - Document processing framework
- [ChromaDB](https://trychroma.com) - Vector database
- [Pydantic](https://pydantic.dev) - Data validation

## 📧 Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/your-username/ingestion-pipeline/issues)
- Submit a [pull request](https://github.com/your-username/ingestion-pipeline/pulls)

---

**Built with ❤️ for making document ingestion simple, powerful, and private**
