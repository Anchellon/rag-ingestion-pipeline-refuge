"""
Utility to serialize metadata for ChromaDB compatibility.
ChromaDB only accepts: str, int, float, bool (NO None values or complex types)
"""

from typing import Dict, Any, List
from datetime import datetime
import json

def serialize_for_chromadb(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert metadata to ChromaDB-compatible format.
    
    Rules:
    - Remove None values
    - Convert datetime to ISO string
    - Convert lists/dicts to JSON strings
    - Keep only str, int, float, bool at top level
    
    Args:
        metadata: Raw metadata dictionary
        
    Returns:
        ChromaDB-compatible metadata dictionary
    """
    serialized = {}
    
    for key, value in metadata.items():
        # Skip None values entirely
        if value is None:
            continue
            
        # Handle datetime objects
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
            
        # Handle nested dicts - convert to JSON string
        elif isinstance(value, dict):
            # Only include if dict is not empty
            if value:
                serialized[key] = json.dumps(value)
                
        # Handle lists - convert to JSON string
        elif isinstance(value, list):
            # Only include if list is not empty
            if value:
                serialized[key] = json.dumps(value)
                
        # Handle booleans (must come before int check since bool is subclass of int)
        elif isinstance(value, bool):
            serialized[key] = value
            
        # Handle primitives (str, int, float)
        elif isinstance(value, (str, int, float)):
            serialized[key] = value
            
        # Handle nested Pydantic models
        elif hasattr(value, 'model_dump'):
            dumped = value.model_dump()
            # Recursively serialize and only include if non-empty
            nested = serialize_for_chromadb(dumped)
            if nested:
                serialized[key] = json.dumps(nested)
                
        else:
            # Convert anything else to string as fallback
            serialized[key] = str(value)
    
    return serialized


def flatten_metadata(metadata: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    Flatten nested metadata structure for ChromaDB.
    
    Example:
        {"contact": {"phone": "123"}} -> {"contact_phone": "123"}
    
    Args:
        metadata: Nested metadata dictionary
        prefix: Prefix for flattened keys
        
    Returns:
        Flattened metadata dictionary
    """
    flattened = {}
    
    for key, value in metadata.items():
        new_key = f"{prefix}{key}" if prefix else key

        # Skip None values
        if value is None:
            continue

        # Skip empty dicts
        elif isinstance(value, dict) and not value:
            continue

        # Recursively flatten dicts
        elif isinstance(value, dict):
            flattened.update(flatten_metadata(value, f"{new_key}_"))

        # Skip empty lists
        elif isinstance(value, list) and not value:
            continue

        # Convert lists to JSON strings
        elif isinstance(value, list):
            flattened[new_key] = json.dumps(value)

        # Handle datetime
        elif isinstance(value, datetime):
            flattened[new_key] = value.isoformat()

        # Handle Pydantic models
        elif hasattr(value, 'model_dump'):
            dumped = value.model_dump()
            flattened.update(flatten_metadata(dumped, f"{new_key}_"))

        # Keep primitives (bool check must come before int, since bool is subclass of int)
        elif isinstance(value, (str, int, float, bool)):
            flattened[new_key] = value

        else:
            # Convert any other type to string as fallback
            flattened[new_key] = str(value)
    
    return flattened


def prepare_chunk_metadata(chunk_metadata) -> Dict[str, Any]:
    """
    Prepare ChunkMetadata for ChromaDB storage.
    
    This is the main function to use in your pipeline.
    
    Args:
        chunk_metadata: ChunkMetadata Pydantic model
        
    Returns:
        ChromaDB-compatible metadata dictionary
    """
    # Convert Pydantic model to dict
    metadata_dict = chunk_metadata.model_dump()
    
    # Option 1: Flatten everything (recommended for easy querying)
    # This converts nested structures to flat keys
    flattened = flatten_metadata(metadata_dict)
    
    # Option 2: Keep structure but serialize complex types
    # Uncomment below if you prefer nested JSON strings
    # flattened = serialize_for_chromadb(metadata_dict)
    
    return flattened


# Example usage in your ingestion pipeline:
# 
# from src.utils.metadata_serializer import prepare_chunk_metadata
# 
# # In your enrichment step:
# for chunk in chunks:
#     chunk_metadata = ChunkMetadata(...)
#     
#     # Prepare metadata for ChromaDB
#     chromadb_metadata = prepare_chunk_metadata(chunk_metadata)
#     
#     # Store with LangChain Document
#     document = Document(
#         page_content=chunk.page_content,
#         metadata=chromadb_metadata
#     )