"""
Test cases for LLM metadata extraction
"""
import pytest
import json


@pytest.mark.unit
@pytest.mark.llm
class TestLLMExtraction:
    """Test suite for LLM metadata extraction"""

    def test_basic_extraction(self, llm_extractor, simple_service_text):
        """Test LLM extractor with simple, clear service text"""
        # Extract metadata
        metadata = llm_extractor.extract(simple_service_text)

        # Verify core fields
        assert metadata.service_type == "food", \
            f"Expected service_type='food', got '{metadata.service_type}'"
        assert metadata.city == "San Francisco", \
            f"Expected city='San Francisco', got '{metadata.city}'"

        # Verify contact information
        assert metadata.contact is not None, "Expected contact to be extracted"
        assert metadata.contact.phone == "(415) 555-1234", \
            f"Expected phone='(415) 555-1234', got '{metadata.contact.phone}'"

        # Verify location
        assert metadata.location is not None, "Expected location to be extracted"
        assert "123 Main Street" in metadata.location.address or \
               "123 Main St" in metadata.location.address, \
            f"Expected address with '123 Main', got '{metadata.location.address}'"

        # Verify services mentioned
        assert metadata.mentioned_services is not None, \
            "Expected mentioned_services to be extracted"

    def test_pdf_extraction(self, llm_extractor, sample_pdf_content):
        """Test LLM extractor with actual PDF content"""
        first_page = sample_pdf_content[0].page_content

        # Extract metadata
        metadata = llm_extractor.extract(first_page)

        # Verify at least some data was extracted
        has_data = any([
            metadata.service_type is not None,
            metadata.city is not None,
            metadata.mentioned_services is not None,
            metadata.mentioned_organizations is not None,
            metadata.contact is not None,
            metadata.location is not None
        ])

        assert has_data, \
            "Expected at least some metadata to be extracted from PDF"

        # If service_type was extracted, verify it makes sense
        if metadata.service_type:
            valid_types = ["food", "housing", "healthcare", "legal",
                          "education", "employment", "general", "other"]
            assert metadata.service_type in valid_types, \
                f"Invalid service_type: {metadata.service_type}"

    def test_llm_response_format(self, llm_extractor, simple_service_text):
        """Test that LLM returns valid JSON (not schema)"""
        # Get raw LLM response
        formatted_prompt = llm_extractor.prompt.format(text=simple_service_text)
        result = llm_extractor.llm.invoke(formatted_prompt)

        raw_response = result.content if hasattr(result, 'content') else str(result)

        # Clean and parse response
        cleaned = llm_extractor._clean_response(raw_response)

        # Should be valid JSON
        parsed = json.loads(cleaned)

        # Should not be a schema (schemas have "$defs" or "properties" at root)
        assert "$defs" not in parsed, \
            "LLM returned a schema instead of data (found '$defs')"
        assert "properties" not in parsed or isinstance(parsed.get("properties"), str), \
            "LLM returned a schema instead of data (found 'properties' dict)"

        # Should have actual data values
        has_values = any([
            isinstance(v, str) and v and v != "null"
            for v in parsed.values()
            if v is not None
        ])
        assert has_values, "LLM returned structure without actual data values"

    def test_empty_text_handling(self, llm_extractor):
        """Test LLM behavior with empty or minimal text"""
        minimal_text = "Test document."

        # Should not crash
        metadata = llm_extractor.extract(minimal_text)

        # Should return ExtractedMetadata object
        assert metadata is not None
        # Most fields should be None for minimal text
        assert metadata.service_type is None or metadata.service_type == "general"

    @pytest.mark.slow
    def test_extraction_consistency(self, llm_extractor, simple_service_text):
        """Test that extraction is consistent across multiple calls"""
        # Extract twice
        metadata1 = llm_extractor.extract(simple_service_text)
        metadata2 = llm_extractor.extract(simple_service_text)

        # Key fields should be consistent (with temperature=0)
        assert metadata1.service_type == metadata2.service_type, \
            "service_type inconsistent across runs"
        assert metadata1.city == metadata2.city, \
            "city inconsistent across runs"

    def test_contact_extraction(self, llm_extractor):
        """Test extraction of various contact formats"""
        text_with_contact = """
        Oakland Food Bank
        Phone: 510-555-1234
        Email: info@oaklandfood.org
        Website: www.oaklandfood.org
        """

        metadata = llm_extractor.extract(text_with_contact)

        if metadata.contact:
            # At least phone should be extracted
            assert metadata.contact.phone is not None, \
                "Expected phone to be extracted"

    def test_location_extraction(self, llm_extractor):
        """Test extraction of location details"""
        text_with_location = """
        Community Center
        Address: 456 Broadway, Oakland, CA 94612
        Serves the Temescal neighborhood
        """

        metadata = llm_extractor.extract(text_with_location)

        # Verify location extraction
        if metadata.location:
            assert "Oakland" in (metadata.location.city or ""), \
                "Expected city to be extracted"
            assert metadata.location.state == "CA" or metadata.city == "Oakland", \
                "Expected state or city to be extracted"


@pytest.mark.integration
@pytest.mark.llm
class TestLLMExtractionDebug:
    """Debug tests for LLM extraction"""

    def test_llm_raw_response_inspection(self, llm_extractor, sample_pdf_content):
        """Inspect raw LLM response for debugging"""
        first_page = sample_pdf_content[0].page_content

        # Get formatted prompt
        formatted_prompt = llm_extractor.prompt.format(text=first_page)

        # Call LLM
        result = llm_extractor.llm.invoke(formatted_prompt)
        raw_response = result.content if hasattr(result, 'content') else str(result)

        # Print for inspection (captured by pytest)
        print("\n" + "=" * 60)
        print("RAW LLM RESPONSE (first 500 chars):")
        print("-" * 60)
        print(raw_response[:500])
        print("-" * 60)

        # Clean response
        cleaned = llm_extractor._clean_response(raw_response)

        print("\nCLEANED RESPONSE (first 500 chars):")
        print("-" * 60)
        print(cleaned[:500])
        print("-" * 60)

        # Parse JSON
        parsed = json.loads(cleaned)

        print("\nPARSED JSON KEYS:")
        print(list(parsed.keys()))
        print("=" * 60)

        # Assertions
        assert isinstance(parsed, dict), "Response should be a dictionary"
        assert len(parsed) > 0, "Response should not be empty"
