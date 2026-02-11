"""
Pytest configuration and shared fixtures
"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.metadata.llm_extractor import LLMMetadataExtractor
from src.loaders.pdf_loader import PDFLoader
from src.pipeline.ingestion import IngestionPipeline


@pytest.fixture(scope="session")
def config():
    """Load configuration once per test session"""
    return load_config('config/config.yaml')


@pytest.fixture(scope="session")
def llm_extractor(config):
    """Create LLM extractor instance (reused across tests)"""
    return LLMMetadataExtractor(
        model=config['metadata']['llm_model'],
        base_url=config['metadata']['base_url']
    )


@pytest.fixture(scope="session")
def pdf_loader():
    """Create PDF loader instance"""
    return PDFLoader()


@pytest.fixture(scope="session")
def sample_pdf_path():
    """Path to sample PDF for testing"""
    return 'tests/fixtures/sample.pdf'


@pytest.fixture(scope="session")
def sample_pdf_content(pdf_loader, sample_pdf_path):
    """Load sample PDF content once per session"""
    docs = pdf_loader.load(sample_pdf_path)
    return docs


@pytest.fixture(scope="function")
def pipeline(config):
    """Create fresh pipeline instance for each test"""
    return IngestionPipeline(config)


@pytest.fixture
def simple_service_text():
    """Simple service text for testing extraction"""
    return """
    Soup Kitchen A serves hot meals Monday through Wednesday
    from 11:30am to 1:30pm. Located at 123 Main Street in
    downtown San Francisco. Call (415) 555-1234 for more information.
    No ID required, walk-ins welcome.
    """
