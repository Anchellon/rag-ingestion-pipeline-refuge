"""
Test cases for metadata serialization (ChromaDB compatibility)
"""
import pytest
from src.metadata.schema import (
    ChunkMetadata,
    ExtractedMetadata,
    ContactInfo,
    Location,
    ServiceDetails
)
from src.utils.metadata_serializer import prepare_chunk_metadata


@pytest.fixture
def full_chunk_metadata():
    """Chunk metadata with full nested structures"""
    return ChunkMetadata(
        source_filename="test.pdf",
        source_url="https://example.com/test.pdf",
        page_number=1,
        chunk_index=0,
        token_count=450,
        document_type="brochure",
        source_type="service_info",
        extracted=ExtractedMetadata(
            service_type="food",
            city="San Francisco",
            neighborhood="Mission District",
            mentioned_services=["Food Bank", "Soup Kitchen"],
            mentioned_organizations=["SF Food Bank"],
            contact=ContactInfo(
                phone="415-555-1234",
                email="info@example.com",
                website="https://example.com"
            ),
            location=Location(
                address="123 Main St",
                city="San Francisco",
                state="CA",
                zip="94102",
                neighborhood="Mission District"
            ),
            service_details=ServiceDetails(
                hours={"monday": "9am-5pm", "tuesday": "9am-5pm"},
                eligibility="All welcome",
                cost="Free",
                languages=["English", "Spanish"],
                accessibility="Wheelchair accessible"
            )
        )
    )


@pytest.fixture
def minimal_chunk_metadata():
    """Chunk metadata with minimal data (service in DB)"""
    return ChunkMetadata(
        source_filename="test2.pdf",
        page_number=2,
        chunk_index=1,
        token_count=350,
        document_type="brochure",
        extracted=ExtractedMetadata(
            related_service_id=123,
            service_type="housing",
            city="Oakland",
            contact=None,
            location=None
        )
    )


@pytest.mark.unit
class TestMetadataSerialization:
    """Test suite for metadata serialization"""

    def test_full_metadata_serialization(self, full_chunk_metadata):
        """Test serialization with full nested structures"""
        # Serialize for ChromaDB
        chromadb_metadata = prepare_chunk_metadata(full_chunk_metadata)

        # Validate no None values
        none_values = {k: v for k, v in chromadb_metadata.items() if v is None}
        assert len(none_values) == 0, f"Found None values: {none_values}"

        # Validate no nested structures (dict/list)
        nested = {
            k: type(v).__name__
            for k, v in chromadb_metadata.items()
            if isinstance(v, (dict, list))
        }
        assert len(nested) == 0, f"Found nested structures: {nested}"

        # Verify key fields exist and are flattened
        assert "source_filename" in chromadb_metadata
        assert chromadb_metadata["source_filename"] == "test.pdf"

        assert "extracted_service_type" in chromadb_metadata
        assert chromadb_metadata["extracted_service_type"] == "food"

        assert "extracted_city" in chromadb_metadata
        assert chromadb_metadata["extracted_city"] == "San Francisco"

        assert "extracted_contact_phone" in chromadb_metadata
        assert chromadb_metadata["extracted_contact_phone"] == "415-555-1234"

        assert "extracted_location_address" in chromadb_metadata
        assert chromadb_metadata["extracted_location_address"] == "123 Main St"

    def test_minimal_metadata_serialization(self, minimal_chunk_metadata):
        """Test serialization with minimal data"""
        chromadb_metadata = prepare_chunk_metadata(minimal_chunk_metadata)

        # Validate ChromaDB compatibility
        assert all(v is not None for v in chromadb_metadata.values()), \
            "Found None values"
        assert all(not isinstance(v, (dict, list)) for v in chromadb_metadata.values()), \
            "Found nested structures"

        # Verify key fields
        assert chromadb_metadata["source_filename"] == "test2.pdf"
        assert chromadb_metadata["extracted_service_type"] == "housing"
        assert chromadb_metadata["extracted_city"] == "Oakland"
        assert chromadb_metadata["extracted_related_service_id"] == 123

    def test_empty_collections_removed(self):
        """Test that empty dicts and lists are properly removed"""
        chunk_metadata = ChunkMetadata(
            source_filename="test3.pdf",
            page_number=1,
            chunk_index=0,
            token_count=100,
            extracted=ExtractedMetadata(
                service_type="general",
                city="Berkeley",
                mentioned_services=[],  # Empty list
                mentioned_organizations=[],  # Empty list
                contact=None,
                location=None,
                service_details=None
            )
        )

        chromadb_metadata = prepare_chunk_metadata(chunk_metadata)

        # Empty lists should be removed
        assert "extracted_mentioned_services" not in chromadb_metadata
        assert "extracted_mentioned_organizations" not in chromadb_metadata

        # None values should be removed
        assert all(v is not None for v in chromadb_metadata.values())

    def test_datetime_serialization(self):
        """Test that datetime fields are converted to ISO format strings"""
        chunk_metadata = ChunkMetadata(
            source_filename="test4.pdf",
            chunk_index=0,
            token_count=100
        )

        chromadb_metadata = prepare_chunk_metadata(chunk_metadata)

        # extracted_date should be a string (ISO format)
        assert "extracted_date" in chromadb_metadata
        assert isinstance(chromadb_metadata["extracted_date"], str)
        # Should be valid ISO format (contains 'T' separator)
        assert 'T' in chromadb_metadata["extracted_date"]

    def test_all_primitives(self, full_chunk_metadata):
        """Test that all values are primitives (str, int, float, bool)"""
        chromadb_metadata = prepare_chunk_metadata(full_chunk_metadata)

        allowed_types = (str, int, float, bool)
        for key, value in chromadb_metadata.items():
            assert isinstance(value, allowed_types), \
                f"Field '{key}' has invalid type {type(value).__name__} (value: {value})"
