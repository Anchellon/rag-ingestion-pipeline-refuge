from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

class PDFLoader:
    """Load PDF files using LangChain's PyPDFLoader"""
    
    def __init__(self):
        pass
    
    def load(self, file_path: str) -> List[Document]:
        """
        Load PDF and return list of Document objects
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of Document objects, one per page
            Each has: page_content (text) and metadata (page number, source)
        """
        # Validate file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        # Load PDF using LangChain
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Add source filename to metadata
        for doc in documents:
            doc.metadata['source_filename'] = str(Path(file_path).name)
            doc.metadata['source_path'] = str(file_path)
        
        return documents