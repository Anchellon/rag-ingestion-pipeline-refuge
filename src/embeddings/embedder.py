import json
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
        self._bedrock_client = None

        if provider != "bedrock":
            self._lc_embeddings = self._init_lc_embeddings()

    def _init_lc_embeddings(self):
        if self.provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(model=self.model, base_url=self.base_url)
        raise ValueError(f"Unsupported embedding provider: '{self.provider}'")

    def _get_bedrock_client(self):
        if self._bedrock_client is None:
            import boto3
            self._bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
            )
        return self._bedrock_client

    def _embed_one_bedrock(self, text: str) -> List[float]:
        # We call boto3 directly instead of using langchain_aws.BedrockEmbeddings
        # because langchain_aws has its own internal retry loop (4 attempts with
        # short delays). By the time it raises ThrottlingException to our code it
        # has already burned 4 retries, and our outer backoff then triggers another
        # 4 internal retries on the next call — two uncoordinated retry loops.
        # Using boto3 directly gives us a single, predictable retry loop.
        client = self._get_bedrock_client()
        for attempt in range(8):
            try:
                response = client.invoke_model(
                    modelId=self.model,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({"inputText": text}),
                )
                return json.loads(response['body'].read())['embedding']
            except client.exceptions.ThrottlingException:
                wait = min(2 ** attempt + random.uniform(0, 1), 60)
                print(f"  Bedrock throttled — retrying in {wait:.1f}s (attempt {attempt + 1})")
                time.sleep(wait)
            except Exception:
                raise
        raise RuntimeError("Bedrock throttling: exceeded max retries")

    def embed_text(self, text: str) -> List[float]:
        if self.provider == "bedrock":
            return self._embed_one_bedrock(text)
        return self._lc_embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "bedrock":
            results = []
            for text in texts:
                results.append(self._embed_one_bedrock(text))
                time.sleep(0.1)  # 10 req/s steady state — stays under Bedrock quota
            return results
        return self._lc_embeddings.embed_documents(texts)
