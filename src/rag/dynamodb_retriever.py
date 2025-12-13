"""
DynamoDB-based retriever for semantic search over knowledge base.

"""

import os
from typing import Optional, List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ..config import get_embedding_config
from ..vectorstores.dynamodb_vector_store import DynamoDBVectorStore
from ..loaders.knowledge_base import load_knowledge_base

# Global retriever cache (cold start optimization)
_vector_store: Optional[DynamoDBVectorStore] = None
_embeddings: Optional[Embeddings] = None


def _get_embeddings() -> Embeddings:
    """
    Get embeddings instance based on configuration.

    Returns:
        Configured embeddings instance

    Raises:
        ImportError: If required package not installed
        ValueError: If backend not supported or credentials missing
    """
    global _embeddings

    if _embeddings is not None:
        return _embeddings

    config = get_embedding_config()
    backend = config["backend"]
    model_id = config["model_id"]
    aws_region = config["aws_region"]

    if backend == "bedrock":
        try:
            from langchain_aws import BedrockEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-aws not installed. Install with: pip install langchain-aws"
            )

        print(f"Using Bedrock embeddings: {model_id}")

        _embeddings = BedrockEmbeddings(
            model_id=model_id,
            region_name=aws_region
        )
        return _embeddings

    elif backend == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. Install with: pip install langchain-openai"
            )

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set for OpenAI backend")

        print(f"Using OpenAI embeddings: {model_id}")

        _embeddings = OpenAIEmbeddings(
            model=model_id,
            openai_api_key=api_key
        )
        return _embeddings

    else:
        raise ValueError(f"Unsupported embedding backend: {backend}")


def _initialize_vector_store() -> DynamoDBVectorStore:
    """
    Initialize DynamoDB vector store and load knowledge base if empty.

    Returns:
        Initialized DynamoDBVectorStore
    """
    table_name = os.environ.get('DYNAMODB_TABLE', 'virtual-me-vectors-prod')
    region = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-3')

    vector_store = DynamoDBVectorStore(table_name=table_name, region=region)

    # Check if vector store is empty (needs initialization)
    if vector_store.count() == 0:
        print("DynamoDB vector store is empty, initializing...")

        # Load knowledge base documents
        documents = load_knowledge_base()
        print(f"Loaded {len(documents)} documents from knowledge base")

        # Get embeddings
        embeddings = _get_embeddings()

        # Generate embeddings for all documents
        print("Generating embeddings...")
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Batch embed all texts
        embedding_vectors = embeddings.embed_documents(texts)

        # Store in DynamoDB
        print("Storing vectors in DynamoDB...")
        vector_store.add_documents(texts, embedding_vectors, metadatas)
        print(f"Initialized DynamoDB with {len(texts)} vectors")
    else:
        print(f"DynamoDB vector store already initialized ({vector_store.count()} vectors)")

    return vector_store


def get_retriever(top_k: int = 3):
    """
    Get or create the DynamoDB retriever.

    This function implements cold start optimization by caching the vector store
    at module level. The first call initializes the store, subsequent calls return
    the cached instance.

    Args:
        top_k: Number of most relevant documents to retrieve

    Returns:
        Retriever-like object with get_relevant_documents method

    Example:
        >>> retriever = get_retriever(top_k=3)
        >>> docs = retriever.get_relevant_documents("What is your experience?")
        >>> len(docs) <= 3
        True
    """
    global _vector_store

    # Return cached vector store if available
    if _vector_store is None:
        print("Initializing DynamoDB retriever...")
        _vector_store = _initialize_vector_store()
        print("Retriever initialized")

    # Return a retriever wrapper
    return DynamoDBRetriever(_vector_store, _get_embeddings(), top_k)


class DynamoDBRetriever:
    """
    Retriever wrapper for DynamoDB vector store.
    Compatible with LangChain retriever interface.
    """

    def __init__(self, vector_store: DynamoDBVectorStore, embeddings: Embeddings, top_k: int = 3):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.top_k = top_k

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve most relevant documents for a query.

        Args:
            query: User question

        Returns:
            List of relevant Document objects
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Search in DynamoDB
        results = self.vector_store.similarity_search(query_embedding, k=self.top_k)

        # Convert to LangChain Document objects
        documents = [
            Document(page_content=text, metadata={"score": score})
            for text, score in results
        ]

        return documents


def reset_retriever() -> None:
    """
    Reset the cached retriever.

    Useful for testing or if knowledge base is updated.
    """
    global _vector_store, _embeddings
    _vector_store = None
    _embeddings = None
    print("Retriever cache cleared")
