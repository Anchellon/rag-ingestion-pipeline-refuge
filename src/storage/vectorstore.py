
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Optional, Dict

class VectorStore:
    """Handle ChromaDB vector storage operations"""

    def __init__(
        self,
        embeddings,
        collection_name: str = "pdf-documents",
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize ChromaDB vector store

        Args:
            embeddings: Embedding function (from Embedder)
            collection_name: Name of ChromaDB collection
            persist_directory: Where to store ChromaDB data
        """
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.store = self._init_store()

    def _init_store(self):
        """Initialize ChromaDB with a persistent client (chromadb 1.x API)"""
        client = chromadb.PersistentClient(path=self.persist_directory)
        return Chroma(
            client=client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to vector store
        
        Args:
            documents: List of LangChain Document objects
                      Each should have page_content and metadata
        
        Returns:
            List of document IDs
        """
        ids = self.store.add_documents(documents)
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            k: Number of results to return
            filter: Metadata filters (e.g., {"city": "San Francisco"})
        
        Returns:
            List of matching Document objects
        """
        return self.store.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
    
    def delete_collection(self):
        """Delete the entire collection (use with caution!)"""
        self.store.delete_collection()