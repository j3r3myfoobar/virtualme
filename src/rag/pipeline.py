"""
LangGraph RAG pipeline orchestration.

Implements the complete Retrieval Augmented Generation workflow
using LangGraph state machine.
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END

from .state import GraphState
from .retriever import get_retriever
from .generator import generate_response
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def retrieve_node(state: GraphState) -> Dict[str, str]:
    """
    Retrieval Node: Queries the FAISS vector store for relevant context.

    Args:
        state: Current graph state containing the user question

    Returns:
        Dictionary with retrieved context

    Example:
        >>> state = {"question": "What is your experience?", ...}
        >>> result = retrieve_node(state)
        >>> "context" in result
        True
    """
    question = state["question"]

    # Get retriever and fetch relevant documents
    retriever = get_retriever()
    documents: List[Document] = retriever.get_relevant_documents(question)

    # Format context from retrieved documents
    context = format_context(documents)

    logger.debug("documents_retrieved",
                document_count=len(documents),
                context_length=len(context))

    return {"context": context}


def generate_node(state: GraphState) -> Dict[str, List[AIMessage]]:
    """
    Generation Node: Uses LLM to generate response based on retrieved context.

    Args:
        state: Current graph state with context and question

    Returns:
        Dictionary with AI message response

    Example:
        >>> state = {
        ...     "context": "I have 8 years experience...",
        ...     "question": "What is your experience?",
        ...     ...
        ... }
        >>> result = generate_node(state)
        >>> "messages" in result
        True
    """
    context = state["context"]
    question = state["question"]

    # Generate response using LLM
    response_text = generate_response(context, question)

    return {"messages": [AIMessage(content=response_text)]}


def format_context(documents: List[Document]) -> str:
    """
    Format retrieved documents into a context string.

    Args:
        documents: List of retrieved Document objects

    Returns:
        Formatted context string with section headers

    Example:
        >>> docs = [Document(page_content="text", metadata={"Header 2": "Experience"})]
        >>> context = format_context(docs)
        >>> "Experience" in context
        True
    """
    return "\n\n".join([
        f"Section: {doc.metadata.get('Header 2', 'N/A')}\n{doc.page_content}"
        for doc in documents
    ])


def build_graph() -> Any:
    """
    Construct the LangGraph state machine for RAG workflow.

    Flow: START -> retrieve_node -> generate_node -> END

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> graph = build_graph()
        >>> result = graph.invoke({"messages": [], "context": "", "question": "test"})
        >>> "messages" in result
        True
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    # Define edges (flow)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# Compile the graph once at module level (cold start optimization)
_graph = None


def get_graph() -> Any:
    """
    Get or create the compiled LangGraph workflow.

    Implements cold start optimization by caching the compiled graph.

    Returns:
        Compiled LangGraph workflow
    """
    global _graph

    if _graph is None:
        print("Building LangGraph workflow...")
        _graph = build_graph()
        print("LangGraph workflow ready")

    return _graph


def run_rag_pipeline(question: str) -> str:
    """
    Run the complete RAG pipeline for a user question.

    This is the main entry point for the RAG system. It handles:
    1. Retrieving relevant context from the knowledge base
    2. Generating a response using the LLM

    Args:
        question: User's question

    Returns:
        Generated answer text

    Raises:
        ValueError: If question is empty
        Exception: If pipeline fails

    Example:
        >>> answer = run_rag_pipeline("What is your main expertise?")
        >>> isinstance(answer, str)
        True
    """
    if not question:
        raise ValueError("Question cannot be empty")

    # Initialize state
    initial_state: GraphState = {
        "messages": [],
        "context": "",
        "question": question
    }

    # Run the graph
    graph = get_graph()
    result = graph.invoke(initial_state)

    # Extract AI response
    ai_messages = result.get("messages", [])
    if not ai_messages:
        raise Exception("No response generated from pipeline")

    return ai_messages[-1].content
