from pathlib import Path
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.utils.metadata_serializer import prepare_chunk_metadata

from ..loaders.pdf_loader import PDFLoader
from ..metadata.llm_extractor import LLMMetadataExtractor
from ..metadata.schema import ChunkMetadata, ExtractedMetadata
from ..embeddings.embedder import Embedder
from ..storage.vectorstore import VectorStore


class IngestionPipeline:
    """Main pipeline for ingesting PDFs into ChromaDB"""
    
    def __init__(self, config: dict):
        """
        Initialize pipeline with configuration
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        
        # Initialize components
        print("Initializing pipeline components...")
        
        self.loader = PDFLoader()
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunking']['chunk_size'],
            chunk_overlap=config['chunking']['overlap'],
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.metadata_extractor = LLMMetadataExtractor(
            provider=config['metadata']['provider'],
            model=config['metadata']['llm_model'],
            base_url=config['metadata']['base_url']
        )
        
        self.embedder = Embedder(
            provider=config['embeddings']['provider'],
            model=config['embeddings']['model'],
            base_url=config['embeddings']['base_url']
        )
        
        self.vectorstore = VectorStore(
            embeddings=self.embedder.embeddings,
            collection_name=config['vectorstore']['params']['collection_name'],
            persist_directory=config['vectorstore']['params']['persist_directory']
        )
        
        print("✓ Pipeline initialized")
    
    def process_pdf(self, file_path: str) -> Dict:
        """
        Process a single PDF through the pipeline
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with processing results
        """
        print(f"\n{'='*60}")
        print(f"Processing: {file_path}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Load PDF
            print("\n[1/5] Loading PDF...")
            documents = self.loader.load(file_path)
            print(f"  ✓ Loaded {len(documents)} pages")
            
            if not documents:
                raise ValueError("No content extracted from PDF")
            
            # Step 2: Split into chunks
            print("\n[2/5] Splitting into chunks...")
            chunks = self.text_splitter.split_documents(documents)
            print(f"  ✓ Created {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Step 3: Extract metadata (from first chunk as sample)
            print("\n[3/5] Extracting metadata...")
            try:
                first_chunk_text = chunks[0].page_content
                extracted_metadata = self.metadata_extractor.extract(first_chunk_text)
                print(f"  ✓ Extracted metadata")
                print(f"    - Service Type: {extracted_metadata.service_type}")
                print(f"    - City: {extracted_metadata.city}")
                print(f"    - Mentioned Services: {extracted_metadata.mentioned_services}")
            except Exception as e:
                print(f"  ⚠️ Metadata extraction failed: {e}")
                print(f"  → Using empty metadata")
                extracted_metadata = ExtractedMetadata()
            
            # Step 4: Enrich chunks with metadata
            print("\n[4/5] Enriching chunks with metadata...")
            enriched_chunks = self._enrich_chunks(
                chunks=chunks,
                extracted_metadata=extracted_metadata,
                source_filename=Path(file_path).name
            )
            print(f"  ✓ Enriched {len(enriched_chunks)} chunks")
            
            # Debug first chunk
            if enriched_chunks:
                self._debug_metadata(enriched_chunks)
            
            # Step 5: Store in vector database
            print("\n[5/5] Storing in ChromaDB...")
            ids = self.vectorstore.add_documents(enriched_chunks)
            print(f"  ✓ Stored {len(ids)} chunks")
            
            # Summary
            result = {
                'file': file_path,
                'pages': len(documents),
                'chunks': len(enriched_chunks),
                'service_type': extracted_metadata.service_type,
                'city': extracted_metadata.city,
                'chunk_ids': ids,
                'status': 'success'
            }
            
            print(f"\n{'='*60}")
            print(f"✓ Processing complete!")
            print(f"  Pages: {result['pages']}")
            print(f"  Chunks: {result['chunks']}")
            print(f"  Service Type: {result['service_type']}")
            print(f"  City: {result['city']}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"\n✗ Error processing {file_path}: {e}")
            return {
                'file': file_path,
                'status': 'failed',
                'error': str(e)
            }
    
    def process_directory(self, directory: str) -> List[Dict]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Path to directory containing PDFs
            
        Returns:
            List of results for each PDF
        """
        results = []
        pdf_files = list(Path(directory).glob('**/*.pdf'))
        
        print(f"\nFound {len(pdf_files)} PDF files in {directory}")
        
        for pdf_file in pdf_files:
            result = self.process_pdf(str(pdf_file))
            results.append(result)
        
        # Summary statistics
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful
        
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"  Total PDFs: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"{'='*60}\n")
        
        return results
    
    def _enrich_chunks(
        self, 
        chunks: List[Document], 
        extracted_metadata: ExtractedMetadata,
        source_filename: str
    ) -> List[Document]:
        """
        Enrich chunks with extracted metadata
        
        Args:
            chunks: Document chunks from text splitter
            extracted_metadata: Metadata extracted by LLM
            source_filename: Name of the source PDF file
            
        Returns:
            List of Document objects with ChromaDB-compatible metadata
        """
        enriched = []
        
        for i, chunk in enumerate(chunks):
            # Create complete metadata object
            chunk_metadata = ChunkMetadata(
                # Source information
                source_filename=source_filename,
                source_url=chunk.metadata.get('source_url'),
                page_number=chunk.metadata.get('page'),
                
                # Document classification
                document_type=self._infer_document_type(chunk.page_content),
                source_type="service_info",  # Could be made configurable
                
                # Extracted metadata from LLM
                extracted=extracted_metadata,
                
                # Chunk information
                chunk_index=i,
                token_count=len(chunk.page_content.split()),
            )
            
            # *** CRITICAL: Serialize metadata for ChromaDB compatibility ***
            chromadb_metadata = prepare_chunk_metadata(chunk_metadata)
            
            # Create new document with serialized metadata
            enriched_doc = Document(
                page_content=chunk.page_content,
                metadata=chromadb_metadata
            )
            
            enriched.append(enriched_doc)
        
        return enriched
    
    def _infer_document_type(self, text: str) -> str:
        """
        Infer document type from content
        
        Args:
            text: Text content to analyze
            
        Returns:
            Document type string
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['brochure', 'services offered']):
            return 'brochure'
        elif any(word in text_lower for word in ['guide', 'how to', 'step by step']):
            return 'guide'
        elif any(word in text_lower for word in ['policy', 'regulation', 'law']):
            return 'policy'
        elif any(word in text_lower for word in ['flyer', 'announcement']):
            return 'flyer'
        else:
            return 'unknown'
    
    def _debug_metadata(self, enriched_chunks: List[Document]) -> None:
        """
        Debug function to inspect metadata structure
        
        Args:
            enriched_chunks: List of enriched documents to inspect
        """
        print("\n" + "="*60)
        print("METADATA DEBUG")
        print("="*60)
        
        # Check first 2 chunks
        for i, chunk in enumerate(enriched_chunks[:2]):
            print(f"\n--- Chunk {i} ---")
            print(f"Content length: {len(chunk.page_content)} chars")
            print(f"\nMetadata keys ({len(chunk.metadata)} total):")
            
            # Check for problematic values
            none_fields = []
            nested_fields = []
            
            for key, value in chunk.metadata.items():
                value_type = type(value).__name__
                
                # Check for None values (ChromaDB doesn't like these)
                if value is None:
                    none_fields.append(key)
                
                # Check for nested structures (should be flattened)
                if isinstance(value, (dict, list)):
                    nested_fields.append(key)
                
                # Show first few fields
                if i == 0:  # Only for first chunk
                    value_preview = str(value)[:80]
                    print(f"  {key}: {value_type} = {value_preview}")
            
            # Warnings
            if none_fields:
                print(f"\n⚠️  WARNING: Found None values in: {none_fields}")
                print("   → These should be removed by prepare_chunk_metadata()")
            
            if nested_fields:
                print(f"\n⚠️  WARNING: Found nested structures in: {nested_fields}")
                print("   → These should be flattened or JSON-stringified")
            
            if not none_fields and not nested_fields:
                print("\n✓ Metadata looks clean!")
        
        print("\n" + "="*60)