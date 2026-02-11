# src/embeddings/embedder.py

from langchain_ollama import OllamaEmbeddings
from typing import List

class Embedder:
    """Generate embeddings using Ollama or other providers"""
    
    def __init__(
        self, 
        provider: str = "ollama", 
        model: str = "nomic-embed-text",
        base_url: str = "http://172.26.64.1:11434"
    ):
        """
        Initialize embedder
        
        Args:
            provider: "ollama" (only supported for now)
            model: embedding model name
            base_url: Ollama server URL
        """
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.embeddings = self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize the embedding model based on provider"""
        if self.provider == "ollama":
            return OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url
            )
        else:
            raise ValueError(f"Provider '{self.provider}' not supported yet")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts (batch)
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)