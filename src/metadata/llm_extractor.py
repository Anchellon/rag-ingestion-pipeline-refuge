from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
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
                format="json"
            )
        else:
            raise ValueError(f"Provider '{self.provider}' not supported yet")
    
    def _create_prompt(self):
        """Create extraction prompt"""
        template = """You are a metadata extraction system. You MUST respond with ONLY valid JSON.

Document text:
{text}

{format_instructions}

EXTRACTION RULES:
1. Extract ALL information present in the text
2. Contact information:
   - phone numbers → contact.phone
   - emails → contact.email  
   - websites → contact.website
3. Location details:
   - street address → location.address
   - city → location.city
   - state → location.state
   - zip code → location.zip
   - neighborhood → location.neighborhood
4. Service type must be one of: food, housing, healthcare, legal, education, employment, general, other
5. Service names → mentioned_services list
6. Organization names → mentioned_organizations list

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the JSON object
- NO explanations, NO code, NO markdown
- NO ```json``` code blocks
- Start with {{ and end with }}
- Use null (not "null") for missing values
- All strings must be properly quoted

Your response must be valid JSON that can be parsed directly."""

        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )
    
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