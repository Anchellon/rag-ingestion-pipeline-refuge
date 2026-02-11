from src.embeddings.embedder import Embedder
from src.storage.vectorstore import VectorStore
from langchain.schema import Document

# Initialize
embedder = Embedder()
vectorstore = VectorStore(
    embeddings=embedder.embeddings,
    persist_directory="./test_chroma"
)

# Add test documents
docs = [
    Document(
        page_content="Soup kitchen serves meals",
        metadata={"city": "SF", "type": "food"}
    ),
    Document(
        page_content="Shelter provides beds",
        metadata={"city": "Oakland", "type": "housing"}
    )
]

ids = vectorstore.add_documents(docs)
print(f"✓ Added {len(ids)} documents")

# Search
results = vectorstore.similarity_search("food services", k=2)
print(f"✓ Found {len(results)} results")
print(f"✓ Top result: {results[0].page_content}")

# Clean up
vectorstore.delete_collection()
print("✓ Test complete!")
