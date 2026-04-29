import os
from typing import List


class Embedder:
    """Generate embeddings using Bedrock or Ollama"""

    def __init__(
        self,
        provider: str = "bedrock",
        model: str = "amazon.titan-embed-text-v2:0",
        base_url: str = "",
    ):
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.embeddings = self._init_embeddings()

    def _init_embeddings(self):
        if self.provider == "bedrock":
            from langchain_aws import BedrockEmbeddings
            return BedrockEmbeddings(
                model_id=self.model,
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
            )
        elif self.provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url,
            )
        else:
            raise ValueError(f"Unsupported embedding provider: '{self.provider}'")

    def embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
