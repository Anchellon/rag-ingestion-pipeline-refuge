import os
import time
import random
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
        if self.provider != "bedrock":
            return self.embeddings.embed_documents(texts)

        # Bedrock throttles hard under bulk load — embed one at a time with
        # exponential backoff so we stay within the on-demand rate limit.
        results = []
        for text in texts:
            attempts = 0
            while True:
                try:
                    results.append(self.embeddings.embed_query(text))
                    # Small base delay to avoid bursting
                    time.sleep(0.05)
                    break
                except Exception as e:
                    if "ThrottlingException" in str(e) or "Too many requests" in str(e):
                        attempts += 1
                        wait = min(2 ** attempts + random.uniform(0, 1), 60)
                        print(f"  Bedrock throttled — retrying in {wait:.1f}s (attempt {attempts})")
                        time.sleep(wait)
                    else:
                        raise
        return results
