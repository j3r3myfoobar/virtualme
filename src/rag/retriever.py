"""
FAISS-based retriever for semantic search over knowledge base.

Supports multiple embedding backends:
- AWS Bedrock (Titan, Cohere)
- OpenAI (text-embedding-ada-002)
"""

import os
from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.embeddings import Embeddings

# Import config
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import get_embedding_config
from utils.logger import get_logger

from loaders.knowledge_base import load_knowledge_base

# Initialize logger
logger = get_logger(__name__)

# Global retriever cache (cold start optimization)
_retriever: Optional[VectorStoreRetriever] = None


def _get_embeddings() -> Embeddings:
    """
    Get embeddings instance based on configuration.

    Returns:
        Configured embeddings instance

    Raises:
        ImportError: If required package not installed
        ValueError: If backend not supported or credentials missing
    """
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

        logger.info("bedrock_embeddings_initialized", model_id=model_id, region=aws_region)

        return BedrockEmbeddings(
            model_id=model_id,
            region_name=aws_region
        )

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

        logger.info("openai_embeddings_initialized", model_id=model_id)

        return OpenAIEmbeddings(
            model=model_id,
            openai_api_key=api_key
        )

    else:
        raise ValueError(f"Unsupported embedding backend: {backend}")


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
        ValueError: If credentials not set
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

    # Load and split documents
    logger.info("loading_knowledge_base")
    documents = load_knowledge_base()

    # Get embeddings instance
    logger.info("creating_embeddings")
    embeddings = _get_embeddings()

    # Create FAISS vector store from documents
    logger.info("building_faiss_index")
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Create retriever that returns top_k most relevant chunks
    _retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )

    logger.info("retriever_initialized", top_k=top_k)

    return _retriever


def reset_retriever() -> None:
    """
    Reset the cached retriever.

    Useful for testing or if knowledge base is updated.
    """
    global _retriever
    _retriever = None
    logger.info("retriever_cache_cleared")
