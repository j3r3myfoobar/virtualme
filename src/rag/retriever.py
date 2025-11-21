"""
FAISS-based retriever for semantic search over knowledge base.

Handles creating embeddings and building the FAISS vector store
for efficient similarity search.
"""

import os
from typing import Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever

from loaders.knowledge_base import load_knowledge_base


# Global retriever cache (cold start optimization)
_retriever: Optional[VectorStoreRetriever] = None


def get_retriever(top_k: int = 3) -> VectorStoreRetriever:
    """
    Get or create the FAISS retriever.

    This function implements cold start optimization by caching the retriever
    at module level. The first call builds the index, subsequent calls return
    the cached instance.

    Args:
        top_k: Number of most relevant documents to retrieve

    Returns:
        Configured FAISS retriever

    Raises:
        ValueError: If OPENAI_API_KEY is not set
        Exception: If knowledge base loading or indexing fails

    Example:
        >>> retriever = get_retriever(top_k=3)
        >>> docs = retriever.get_relevant_documents("What is your experience?")
        >>> len(docs)
        3
    """
    global _retriever

    # Return cached retriever if available
    if _retriever is not None:
        return _retriever

    # Verify API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Load and split documents
    print("Loading knowledge base...")
    documents = load_knowledge_base()

    # Initialize OpenAI embeddings
    # Uses text-embedding-ada-002 by default
    print("Creating embeddings...")
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)

    # Create FAISS vector store from documents
    print("Building FAISS index...")
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Create retriever that returns top_k most relevant chunks
    _retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )

    print(f"Retriever initialized (top_k={top_k})")

    return _retriever


def reset_retriever() -> None:
    """
    Reset the cached retriever.

    Useful for testing or if knowledge base is updated.
    """
    global _retriever
    _retriever = None
    print("Retriever cache cleared")
