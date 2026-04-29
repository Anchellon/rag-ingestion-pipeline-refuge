import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def load_config(config_path: str = "config/config.yaml"):
    """
    Load configuration from YAML with optional environment variable overrides.

    YAML provides application defaults. Environment variables take precedence.

    Optional overrides:
        EMBEDDING_PROVIDER  — override embeddings.provider
        EMBEDDING_MODEL     — override embeddings.model
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if os.getenv('EMBEDDING_PROVIDER'):
        config['embeddings']['provider'] = os.getenv('EMBEDDING_PROVIDER')

    if os.getenv('EMBEDDING_MODEL'):
        config['embeddings']['model'] = os.getenv('EMBEDDING_MODEL')

    return config
