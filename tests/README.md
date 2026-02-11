# Ingestion Pipeline Tests

This directory contains pytest test suites for the PDF ingestion pipeline.

## Test Structure

```
tests/
├── __init__.py                      # Package initialization
├── conftest.py                      # Pytest fixtures and configuration
├── README.md                        # This file
├── test_metadata_serialization.py   # Tests for ChromaDB metadata serialization
├── test_llm_extraction.py           # Tests for LLM metadata extraction
├── test_pipeline.py                 # Tests for full pipeline integration
└── fixtures/                        # Test data (PDFs, etc.)
    └── sample.pdf
```

## Installation

Install test dependencies:

```bash
pip install pytest pytest-cov
# Or install all requirements including test dependencies
pip install -r requirements.txt
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# Metadata serialization tests only
pytest tests/test_metadata_serialization.py

# LLM extraction tests only
pytest tests/test_llm_extraction.py

# Pipeline tests only
pytest tests/test_pipeline.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_llm_extraction.py::TestLLMExtraction

# Run a specific test function
pytest tests/test_llm_extraction.py::TestLLMExtraction::test_basic_extraction

# Run tests matching a pattern
pytest -k "extraction"
pytest -k "metadata"
```

### Run Tests by Markers

```bash
# Run only unit tests (fast, no external dependencies)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only LLM tests (requires Ollama)
pytest -m llm

# Exclude slow tests
pytest -m "not slow"

# Combine markers
pytest -m "unit and not slow"
```

### Other Useful Options

```bash
# Stop at first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Run last failed tests only
pytest --lf

# Show print statements
pytest -s

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests with multiple components
- `@pytest.mark.llm` - Tests requiring LLM/Ollama connection
- `@pytest.mark.slow` - Tests that take longer to run

## Test Suites

### 1. Metadata Serialization (`test_metadata_serialization.py`)

**Markers**: `unit`

Tests that metadata is properly serialized for ChromaDB compatibility:
- Full nested structures (contact, location, service details)
- Minimal metadata (service in database)
- Empty collections handling
- Datetime serialization
- All values are primitives

**Key validations:**
- ✓ No `None` values (ChromaDB doesn't accept them)
- ✓ No nested structures (must be flattened)
- ✓ All required fields present
- ✓ Values are str, int, float, or bool only

**Run:** `pytest tests/test_metadata_serialization.py`

### 2. LLM Extraction (`test_llm_extraction.py`)

**Markers**: `unit`, `llm`, `integration`, `slow`

Tests LLM metadata extraction functionality:
- Basic extraction with simple text
- PDF content extraction
- LLM response format validation (not schema)
- Empty text handling
- Extraction consistency
- Contact and location extraction

**Prerequisites:**
- Ollama running at configured base_url
- Model specified in config.yaml available

**Run:** `pytest tests/test_llm_extraction.py -m llm`

### 3. Full Pipeline (`test_pipeline.py`)

**Markers**: `unit`, `integration`, `llm`, `slow`

Tests the complete ingestion pipeline:
- PDF loading
- Pipeline initialization
- Full pipeline execution
- Error handling
- Chunking
- Metadata enrichment
- Component initialization

**Run:** `pytest tests/test_pipeline.py`

## Fixtures

Common fixtures are defined in `conftest.py`:

- `config` - Loaded configuration (session scope)
- `llm_extractor` - LLM extractor instance (session scope)
- `pdf_loader` - PDF loader instance (session scope)
- `sample_pdf_path` - Path to sample PDF
- `sample_pdf_content` - Loaded PDF content (session scope)
- `pipeline` - Fresh pipeline instance (function scope)
- `simple_service_text` - Simple service text for testing

## Expected Test Output

```bash
$ pytest -v

tests/test_metadata_serialization.py::TestMetadataSerialization::test_full_metadata_serialization PASSED
tests/test_metadata_serialization.py::TestMetadataSerialization::test_minimal_metadata_serialization PASSED
tests/test_metadata_serialization.py::TestMetadataSerialization::test_empty_collections_removed PASSED
tests/test_metadata_serialization.py::TestMetadataSerialization::test_datetime_serialization PASSED
tests/test_metadata_serialization.py::TestMetadataSerialization::test_all_primitives PASSED
tests/test_llm_extraction.py::TestLLMExtraction::test_basic_extraction PASSED
tests/test_llm_extraction.py::TestLLMExtraction::test_pdf_extraction PASSED
tests/test_llm_extraction.py::TestLLMExtraction::test_llm_response_format PASSED
tests/test_llm_extraction.py::TestLLMExtraction::test_empty_text_handling PASSED
tests/test_pipeline.py::TestPDFLoading::test_pdf_loader PASSED
tests/test_pipeline.py::TestPDFLoading::test_pdf_loader_nonexistent_file PASSED
tests/test_pipeline.py::TestPDFLoading::test_pdf_content_structure PASSED
tests/test_pipeline.py::TestIngestionPipeline::test_pipeline_initialization PASSED
tests/test_pipeline.py::TestIngestionPipeline::test_full_pipeline_execution PASSED

================================ 14 passed in 12.34s ================================
```

## Coverage Report

Generate HTML coverage report:

```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

Generate terminal coverage report:

```bash
pytest --cov=src --cov-report=term-missing
```

## Troubleshooting

### LLM Tests Failing

```bash
# Check Ollama is running
curl http://172.26.64.1:11434/api/tags

# List available models
ollama list

# Verify model name in config
cat config/config.yaml | grep llm_model
```

### Import Errors

```bash
# Ensure you're in project root
pwd

# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### PDF Tests Failing

```bash
# Check sample PDF exists
ls tests/fixtures/sample.pdf

# Verify pypdf is installed
python -c "import pypdf; print(pypdf.__version__)"
```

### ChromaDB Errors

```bash
# Clear ChromaDB directory if needed
rm -rf chroma_db/

# Reinstall ChromaDB
pip install --upgrade chromadb
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest -m unit
      - name: Upload coverage
        run: pytest --cov=src --cov-report=xml
```

## Best Practices

1. **Run unit tests frequently** - They're fast and catch issues early
2. **Run integration tests before commits** - Ensure everything works together
3. **Use markers to skip slow tests** during development
4. **Check coverage** to identify untested code
5. **Write descriptive test names** - They serve as documentation
6. **Use fixtures** to reduce code duplication
7. **Test edge cases** - Empty inputs, missing data, errors

## Adding New Tests

1. Create test file: `tests/test_<component>.py`
2. Add pytest markers for categorization
3. Use fixtures from `conftest.py`
4. Write clear, descriptive test functions
5. Add assertions with helpful messages
6. Update this README if adding new test category

Example:

```python
import pytest

@pytest.mark.unit
def test_new_feature(config):
    """Test description"""
    # Arrange
    expected = "result"

    # Act
    actual = my_function(config)

    # Assert
    assert actual == expected, f"Expected {expected}, got {actual}"
```
