"""
DynamoDB-based retriever for semantic search over the knowledge base.
"""

import os
from typing import Optional, List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import get_embedding_config
from constants import RAG_TOP_K_CHUNKS, DEFAULT_AWS_REGION, BEDROCK_RETRY_CONFIG
from utils.logging import get_logger
from vectorstores.dynamodb_vector_store import DynamoDBVectorStore
from loaders.knowledge_base import load_knowledge_base

logger = get_logger(__name__)

# Cached instances to avoid cold start overhead
_vector_store: Optional[DynamoDBVectorStore] = None
_embeddings: Optional[Embeddings] = None


def _get_embeddings() -> Embeddings:
    """Get or create embeddings instance."""
    global _embeddings

    if _embeddings is not None:
        return _embeddings

    config = get_embedding_config()

    try:
        from langchain_aws import BedrockEmbeddings
    except ImportError:
        raise ImportError("langchain-aws not installed")

    logger.info("Using Bedrock embeddings: %s", config["model_id"])

    _embeddings = BedrockEmbeddings(
        model_id=config["model_id"],
        region_name=config["aws_region"],
        config=BEDROCK_RETRY_CONFIG
    )
    return _embeddings


def _populate_vector_store(vector_store: DynamoDBVectorStore) -> None:
    """Load knowledge base docs into an empty vector store."""
    documents = load_knowledge_base()
    logger.info("Loaded %d documents", len(documents))

    embeddings = _get_embeddings()
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    logger.info("Generating embeddings...")
    embedding_vectors = embeddings.embed_documents(texts)

    logger.info("Storing in DynamoDB...")
    vector_store.add_documents(texts, embedding_vectors, metadatas)
    logger.info("Stored %d vectors", len(texts))


def _initialize_vector_store() -> DynamoDBVectorStore:
    """Create vector store, populating it if empty."""
    table_name = os.environ.get('DYNAMODB_TABLE', 'virtual-me-vectors-prod')
    region = os.environ.get('AWS_DEFAULT_REGION', DEFAULT_AWS_REGION)

    vector_store = DynamoDBVectorStore(table_name=table_name, region=region)

    if vector_store.count() == 0:
        logger.info("Vector store empty, initializing...")
        _populate_vector_store(vector_store)
    else:
        logger.info("Vector store ready (%d vectors)", vector_store.count())

    return vector_store


def get_retriever(top_k: int = RAG_TOP_K_CHUNKS) -> "DynamoDBRetriever":
    """Get retriever instance (cached for Lambda cold start optimization)."""
    global _vector_store

    if _vector_store is None:
        logger.info("Initializing retriever...")
        _vector_store = _initialize_vector_store()

    return DynamoDBRetriever(_vector_store, _get_embeddings(), top_k)


class DynamoDBRetriever:
    """Wraps DynamoDB vector store with LangChain-compatible interface."""

    def __init__(self, vector_store: DynamoDBVectorStore, embeddings: Embeddings, top_k: int = 3):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.top_k = top_k

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Find the most relevant documents for a query."""
        query_embedding = self.embeddings.embed_query(query)
        results = self.vector_store.similarity_search(query_embedding, k=self.top_k)

        return [
            Document(page_content=text, metadata={"score": score})
            for text, score in results
        ]


def reset_retriever() -> None:
    """Clear cached retriever (for testing or after knowledge base update)."""
    global _vector_store, _embeddings
    _vector_store = None
    _embeddings = None
    logger.info("Retriever cache cleared")
