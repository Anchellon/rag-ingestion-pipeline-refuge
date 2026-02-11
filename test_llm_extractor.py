from src.metadata.llm_extractor import LLMMetadataExtractor
print("Initializing LLM extractor...")
extractor = LLMMetadataExtractor(
    model="llama3.2",
    base_url="http://172.26.64.1:11434"
)
print("✓ LLM extractor initialized")

# Test text
text = """
Soup Kitchen A serves hot meals Monday through Wednesday 
from 11:30am to 1:30pm. Located at 123 Main Street in 
downtown San Francisco. Call (415) 555-1234 for more information.
No ID required, walk-ins welcome.
"""

print("\nExtracting metadata from text...")
print("-" * 50)
print(text.strip())
print("-" * 50)

metadata = extractor.extract(text)

print("\n✓ Extraction complete!")
print("\nExtracted Metadata:")
print(f"  Service Type: {metadata.service_type}")
print(f"  City: {metadata.city}")
print(f"  Contact Phone: {metadata.contact.phone if metadata.contact else None}")
print(f"  Location Address: {metadata.location.address if metadata.location else None}")
print(f"  Mentioned Services: {metadata.mentioned_services}")
print(f"  Mentioned Organizations: {metadata.mentioned_organizations}")

print("\n✓ Test complete!")