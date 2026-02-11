"""
Test cases for the complete ingestion pipeline
"""
import pytest
from pathlib import Path


@pytest.mark.unit
class TestPDFLoading:
    """Test suite for PDF loading"""

    def test_pdf_loader(self, pdf_loader, sample_pdf_path):
        """Test PDF loader functionality"""
        docs = pdf_loader.load(sample_pdf_path)

        assert len(docs) > 0, "Expected at least one page"
        assert docs[0].page_content, "Expected page content to be non-empty"
        assert 'source_filename' in docs[0].metadata, \
            "Expected source_filename in metadata"

    def test_pdf_loader_nonexistent_file(self, pdf_loader):
        """Test PDF loader with non-existent file"""
        with pytest.raises(FileNotFoundError):
            pdf_loader.load('tests/fixtures/nonexistent.pdf')

    def test_pdf_content_structure(self, sample_pdf_content):
        """Test that PDF content has expected structure"""
        assert len(sample_pdf_content) >= 1, "Expected at least 1 page"

        first_page = sample_pdf_content[0]
        assert hasattr(first_page, 'page_content'), \
            "Expected page_content attribute"
        assert hasattr(first_page, 'metadata'), \
            "Expected metadata attribute"
        assert isinstance(first_page.page_content, str), \
            "page_content should be a string"


@pytest.mark.integration
@pytest.mark.llm
class TestIngestionPipeline:
    """Test suite for full ingestion pipeline"""

    def test_pipeline_initialization(self, config):
        """Test pipeline initializes without errors"""
        from src.pipeline.ingestion import IngestionPipeline

        pipeline = IngestionPipeline(config)

        assert pipeline.loader is not None
        assert pipeline.text_splitter is not None
        assert pipeline.metadata_extractor is not None
        assert pipeline.embedder is not None
        assert pipeline.vectorstore is not None

    def test_full_pipeline_execution(self, pipeline, sample_pdf_path):
        """Test complete pipeline execution"""
        result = pipeline.process_pdf(sample_pdf_path)

        # Verify result structure
        assert 'status' in result, "Result should have 'status' field"
        assert 'file' in result, "Result should have 'file' field"
        assert 'chunks' in result, "Result should have 'chunks' field"

        # Verify success
        assert result['status'] == 'success', \
            f"Expected status='success', got '{result['status']}'"

        # Verify chunks were created
        assert result['chunks'] > 0, \
            "Expected at least one chunk to be created"

        # Verify pages were loaded
        assert result.get('pages', 0) > 0, \
            "Expected at least one page to be loaded"

    def test_pipeline_with_nonexistent_file(self, pipeline):
        """Test pipeline error handling with non-existent file"""
        result = pipeline.process_pdf('tests/fixtures/nonexistent.pdf')

        assert result['status'] == 'failed', \
            "Expected status='failed' for non-existent file"
        assert 'error' in result, "Expected error message in result"

    def test_pipeline_chunking(self, pipeline, sample_pdf_path):
        """Test that pipeline creates appropriate chunks"""
        # Load and process
        from src.loaders.pdf_loader import PDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        loader = PDFLoader()
        docs = loader.load(sample_pdf_path)

        config = pipeline.config
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunking']['chunk_size'],
            chunk_overlap=config['chunking']['overlap']
        )

        chunks = splitter.split_documents(docs)

        assert len(chunks) > 0, "Expected at least one chunk"

        # Verify chunk size is reasonable
        for chunk in chunks:
            assert len(chunk.page_content) > 0, "Chunk should have content"
            assert len(chunk.page_content) <= config['chunking']['chunk_size'] * 1.2, \
                "Chunk size should be close to configured size"

    def test_pipeline_metadata_enrichment(self, pipeline, sample_pdf_path):
        """Test that pipeline enriches chunks with metadata"""
        result = pipeline.process_pdf(sample_pdf_path)

        assert result['status'] == 'success'

        # The pipeline should have created chunk_ids
        assert 'chunk_ids' in result, "Expected chunk_ids in result"
        assert len(result['chunk_ids']) > 0, "Expected at least one chunk ID"

    @pytest.mark.slow
    def test_pipeline_directory_processing(self, pipeline, tmp_path):
        """Test processing multiple PDFs in a directory"""
        # This test would need actual PDFs in fixtures
        # For now, we'll skip if directory doesn't have multiple PDFs
        pytest.skip("Requires multiple test PDFs")


@pytest.mark.integration
class TestPipelineComponents:
    """Test individual pipeline components"""

    def test_text_splitter_configuration(self, config):
        """Test text splitter is configured correctly"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunking']['chunk_size'],
            chunk_overlap=config['chunking']['overlap'],
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        test_text = "This is a test. " * 100
        chunks = splitter.split_text(test_text)

        assert len(chunks) > 1, "Long text should be split"
        for chunk in chunks:
            assert len(chunk) <= config['chunking']['chunk_size'] * 1.2

    def test_embedder_initialization(self, config):
        """Test embedder initializes correctly"""
        from src.embeddings.embedder import Embedder

        embedder = Embedder(
            provider=config['embeddings']['provider'],
            model=config['embeddings']['model'],
            base_url=config['embeddings']['base_url']
        )

        assert embedder.embeddings is not None
        assert embedder.model == config['embeddings']['model']

    def test_vectorstore_initialization(self, config):
        """Test vectorstore initializes correctly"""
        from src.embeddings.embedder import Embedder
        from src.storage.vectorstore import VectorStore

        embedder = Embedder(
            provider=config['embeddings']['provider'],
            model=config['embeddings']['model'],
            base_url=config['embeddings']['base_url']
        )

        vectorstore = VectorStore(
            embeddings=embedder.embeddings,
            collection_name=config['vectorstore']['params']['collection_name'],
            persist_directory=config['vectorstore']['params']['persist_directory']
        )

        assert vectorstore.store is not None
        assert vectorstore.collection_name == config['vectorstore']['params']['collection_name']
