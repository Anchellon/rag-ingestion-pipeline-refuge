from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from .schema import ExtractedMetadata
import json
import re

class LLMMetadataExtractor:
    """Extract metadata from text using LLM"""
    
    def __init__(
        self, 
        provider: str = "ollama",
        model: str = "mistral",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize LLM for metadata extraction
        
        Args:
            provider: "ollama" (only supported for now)
            model: LLM model name (mistral, llama3.1, qwen2.5 recommended)
            base_url: Ollama server URL
        """
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.llm = self._init_llm()
        self.parser = PydanticOutputParser(pydantic_object=ExtractedMetadata)
        self.prompt = self._create_prompt()
    
    def _init_llm(self):
        """Initialize the LLM based on provider"""
        if self.provider == "ollama":
            return ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=0,
                format="json",
                timeout=60  # Add 60 second timeout
            )
        else:
            raise ValueError(f"Provider '{self.provider}' not supported yet")
    
    def _create_prompt(self):
        """Create extraction prompt"""
        template = """You are a metadata extraction system. Extract information from the text and return ONLY a JSON object.

Document text:
{text}

EXTRACT THE FOLLOWING (use null for missing values):
- service_type: Category (food, housing, healthcare, legal, education, employment, general, other)
- city: Primary city mentioned
- neighborhood: Neighborhood if mentioned
- mentioned_services: Array of service names mentioned
- mentioned_organizations: Array of organization names mentioned
- contact: Object with phone, email, website (if found)
- location: Object with address, city, state, zip (if found)
- service_details: Object with hours, eligibility, cost, languages, accessibility (if found)

EXAMPLE OUTPUT:
{{
  "service_type": "food",
  "city": "San Francisco",
  "neighborhood": "Mission District",
  "mentioned_services": ["Soup Kitchen", "Food Bank"],
  "mentioned_organizations": ["Fraternite Notre Dame"],
  "contact": {{"phone": "(415) 555-1234", "email": null, "website": "https://example.com"}},
  "location": {{"address": "123 Main St", "city": "San Francisco", "state": "CA", "zip": "94103"}},
  "service_details": {{"hours": {{"monday": "9am-5pm"}}, "eligibility": "All welcome", "cost": "Free"}},
  "related_service_id": null,
  "related_resource_id": null,
  "mentioned_locations": null,
  "topic": null,
  "content_category": null,
  "publication_date": null,
  "publisher": null
}}

CRITICAL:
- Return ONLY the JSON object with actual extracted data
- DO NOT return a schema or template
- Use null for fields you cannot extract
- Start with {{ and end with }}
- NO markdown, NO explanations"""

        return ChatPromptTemplate.from_template(template)
    
    def _clean_response(self, response: str) -> str:
        """
        Clean LLM response to extract valid JSON
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned JSON string
        """
        response = response.strip()
        
        # Remove markdown code blocks
        if '```' in response:
            pattern = r'```(?:json)?\s*(.*?)\s*```'
            match = re.search(pattern, response, re.DOTALL)
            if match:
                response = match.group(1).strip()
        
        # Find first { and last }
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            response = response[start:end+1]
        
        # FIX: Replace string "null" with actual null
        # This handles cases where LLM outputs "null" as a string
        response = re.sub(r':\s*"null"', ': null', response)
        
        return response
        
    def extract(self, text: str) -> ExtractedMetadata:
        """
        Extract metadata from text
        
        Args:
            text: Text chunk to analyze
            
        Returns:
            ExtractedMetadata object
        """
        try:
            # Get raw response from LLM
            result = self.llm.invoke(self.prompt.format(text=text))
            
            # Extract content
            if hasattr(result, 'content'):
                content = result.content
            else:
                content = str(result)
            
            # Clean the response
            cleaned_content = self._clean_response(content)
            
            # Validate it's JSON
            try:
                json.loads(cleaned_content)
            except json.JSONDecodeError as je:
                print(f"JSON validation error: {je}")
                print(f"Cleaned content: {cleaned_content[:500]}")
                raise
            
            # Parse with Pydantic
            parsed_result = self.parser.parse(cleaned_content)
            return parsed_result
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            if 'content' in locals():
                print(f"Raw response: {content[:500]}")
            if 'cleaned_content' in locals():
                print(f"Cleaned response: {cleaned_content[:500]}")
            
            # Return empty metadata on error
            return ExtractedMetadata()