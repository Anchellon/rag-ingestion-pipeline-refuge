import yaml
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_config(config_path: str = "config/config.yaml"):
    """
    Load configuration from YAML file with environment variable overrides.

    YAML provides application defaults.
    Environment variables override for system-specific settings.

    Required environment variables:
        OLLAMA_BASE_URL: Ollama server URL (varies by system: localhost vs WSL IP)

    Optional environment variables (override YAML defaults):
        OLLAMA_LLM_MODEL, OLLAMA_EMBEDDING_MODEL, CHROMA_PERSIST_DIR,
        CHROMA_COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # === REQUIRED: Ollama base URL ===
    # This MUST be set via environment variable for cross-platform compatibility
    ollama_url = os.getenv('OLLAMA_BASE_URL')
    if not ollama_url:
        raise ValueError(
            "OLLAMA_BASE_URL environment variable is required!\n"
            "Create a .env file with: OLLAMA_BASE_URL=http://localhost:11434\n"
            "Or for WSL: OLLAMA_BASE_URL=http://<wsl-ip>:11434"
        )

    config['metadata']['base_url'] = ollama_url
    config['embeddings']['base_url'] = ollama_url

    # === OPTIONAL: Override YAML defaults if env vars are set ===
    if os.getenv('OLLAMA_LLM_MODEL'):
        config['metadata']['llm_model'] = os.getenv('OLLAMA_LLM_MODEL')

    if os.getenv('OLLAMA_EMBEDDING_MODEL'):
        config['embeddings']['model'] = os.getenv('OLLAMA_EMBEDDING_MODEL')

    if os.getenv('CHROMA_PERSIST_DIR'):
        config['vectorstore']['params']['persist_directory'] = os.getenv('CHROMA_PERSIST_DIR')

    if os.getenv('CHROMA_COLLECTION_NAME'):
        config['vectorstore']['params']['collection_name'] = os.getenv('CHROMA_COLLECTION_NAME')

    if os.getenv('CHUNK_SIZE'):
        config['chunking']['chunk_size'] = int(os.getenv('CHUNK_SIZE'))

    if os.getenv('CHUNK_OVERLAP'):
        config['chunking']['overlap'] = int(os.getenv('CHUNK_OVERLAP'))

    return config