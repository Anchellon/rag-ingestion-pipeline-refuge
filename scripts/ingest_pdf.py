# scripts/ingest.py
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.pipeline.ingestion import IngestionPipeline

def main():
    """Main entry point for PDF ingestion"""
    
    print("\n" + "="*60)
    print("PDF INGESTION PIPELINE")
    print("="*60)
    
    # Load configuration
    print("\nLoading configuration...")
    config = load_config('config/config.yaml')
    print("✓ Configuration loaded")
    
    # Initialize pipeline
    pipeline = IngestionPipeline(config)
    
    # Process a single PDF
    # TODO: Replace with your actual PDF path
    pdf_path = 'tests/fixtures/sample.pdf'
    
    if not Path(pdf_path).exists():
        print(f"\n✗ Error: PDF not found at {pdf_path}")
        print("\nPlease either:")
        print(f"  1. Place a PDF at: {pdf_path}")
        print(f"  2. Update the pdf_path variable in this script")
        return
    
    # Process the PDF
    result = pipeline.process_pdf(pdf_path)
    
    # Print summary
    print("\n" + "="*60)
    print("INGESTION COMPLETE")
    print("="*60)
    print(f"\nProcessed: {result['file']}")
    print(f"Chunks created: {result['chunks']}")
    print(f"Service type: {result['service_type']}")
    print(f"City: {result['city']}")
    print(f"\nData stored in: {config['vectorstore']['params']['persist_directory']}")
    print("\n✓ All done!\n")

if __name__ == "__main__":
    main()