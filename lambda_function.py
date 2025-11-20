"""
Virtual Me Chatbot - AWS Lambda Handler
Implements RAG (Retrieval Augmented Generation) pattern using LangGraph
"""

import json
import os
from typing import TypedDict, Annotated, Sequence
from operator import add

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# ============================================================================
# COLD START OPTIMIZATION: Load knowledge base outside handler function
# This ensures the vector store is built only once per Lambda container lifecycle
# ============================================================================

# Global variable to cache the retriever
retriever = None


def load_knowledge_base():
    """
    Load and process the resume.md file into a FAISS vector store.
    This function is called once during Lambda cold start.
    """
    global retriever

    if retriever is not None:
        return retriever

    # Read the resume markdown file
    resume_path = os.path.join(os.path.dirname(__file__), 'resume.md')

    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_content = f.read()

    # Define headers to split on - maintains context hierarchy
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    # Split the markdown maintaining header context
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )

    splits = markdown_splitter.split_text(resume_content)

    # Initialize embeddings - uses OpenAI's text-embedding-ada-002 by default
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.environ.get('OPENAI_API_KEY')
    )

    # Create FAISS vector store from documents
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Create retriever that returns top 3 most relevant chunks
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    return retriever


# Initialize the retriever during cold start
try:
    retriever = load_knowledge_base()
    print("Knowledge base loaded successfully")
except Exception as e:
    print(f"Error loading knowledge base: {str(e)}")
    # Don't fail cold start, but log the error
    retriever = None


# ============================================================================
# LANGGRAPH STATE AND WORKFLOW DEFINITION
# ============================================================================

class GraphState(TypedDict):
    """
    Represents the state of the conversation graph.

    Attributes:
        messages: The conversation history
        context: Retrieved relevant documents from vector store
        question: The current user question
    """
    messages: Annotated[Sequence[BaseMessage], add]
    context: str
    question: str


def retrieve_node(state: GraphState) -> dict:
    """
    Retrieval Node: Queries the FAISS vector store for relevant context.

    Args:
        state: Current graph state containing the user question

    Returns:
        Dictionary with retrieved context
    """
    question = state["question"]

    # Retrieve relevant documents
    documents = retriever.get_relevant_documents(question)

    # Format context from retrieved documents
    context = "\n\n".join([
        f"Section: {doc.metadata.get('Header 2', 'N/A')}\n{doc.page_content}"
        for doc in documents
    ])

    print(f"Retrieved {len(documents)} relevant document chunks")

    return {"context": context}


def generate_node(state: GraphState) -> dict:
    """
    Generation Node: Uses LLM to generate response based on retrieved context.

    Args:
        state: Current graph state with context and question

    Returns:
        Dictionary with AI message response
    """
    context = state["context"]
    question = state["question"]

    # System prompt that defines the chatbot's persona and constraints
    system_prompt = """You are a Virtual Clone chatbot representing the person described in the provided context.

CRITICAL RULES:
1. Answer ONLY based on the provided CONTEXT below
2. If the question cannot be answered from the CONTEXT, say: "I don't have that information in my profile."
3. Respond in first person as if you ARE the person in the resume
4. Be conversational, friendly, and professional
5. Never make up or hallucinate information not present in the CONTEXT
6. Keep responses concise (2-4 sentences unless more detail is explicitly requested)

CONTEXT:
{context}

Remember: You are speaking AS this person, not ABOUT them."""

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Low temperature for more factual responses
        openai_api_key=os.environ.get('OPENAI_API_KEY')
    )

    # Format the full prompt
    prompt = system_prompt.format(context=context)

    # Generate response
    messages = [
        HumanMessage(content=prompt),
        HumanMessage(content=f"Question: {question}")
    ]

    response = llm.invoke(messages)

    return {"messages": [AIMessage(content=response.content)]}


# Build the LangGraph workflow
def build_graph():
    """
    Constructs the LangGraph state machine for RAG workflow.

    Flow: START -> retrieve_node -> generate_node -> END
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
app = build_graph()


# ============================================================================
# LAMBDA HANDLER AND HTTP UTILITIES
# ============================================================================

def http_response(status_code: int, body: dict) -> dict:
    """
    Formats HTTP response with proper CORS headers for API Gateway.

    Args:
        status_code: HTTP status code
        body: Response body dictionary

    Returns:
        Formatted response for API Gateway
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Required for CORS
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(body)
    }


def lambda_handler(event, context):
    """
    Main AWS Lambda handler function.

    Processes POST requests from Deep Chat frontend with conversation history.
    Extracts the latest user message and runs it through the RAG pipeline.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        HTTP response with AI-generated answer
    """

    # Handle CORS preflight requests
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return http_response(200, {'message': 'OK'})

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        messages = body.get('messages', [])

        if not messages:
            return http_response(400, {'error': 'No messages provided'})

        # Extract the last user message (Deep Chat sends full history)
        last_user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_message = msg.get('text', '')
                break

        if not last_user_message:
            return http_response(400, {'error': 'No user message found'})

        # Check if retriever is initialized
        if retriever is None:
            return http_response(500, {
                'error': 'Knowledge base not initialized. Check Lambda logs.'
            })

        # Run the RAG pipeline through LangGraph
        initial_state = {
            "messages": [],
            "context": "",
            "question": last_user_message
        }

        result = app.invoke(initial_state)

        # Extract AI response
        ai_messages = result.get("messages", [])
        if not ai_messages:
            return http_response(500, {'error': 'No response generated'})

        ai_response = ai_messages[-1].content

        # Format response for Deep Chat
        response_body = {
            'text': ai_response
        }

        return http_response(200, response_body)

    except json.JSONDecodeError:
        return http_response(400, {'error': 'Invalid JSON in request body'})

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return http_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })


# ============================================================================
# LOCAL TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Local testing script. Set OPENAI_API_KEY environment variable before running.

    Usage: python lambda_function.py
    """
    # Mock event for testing
    test_event = {
        'body': json.dumps({
            'messages': [
                {'role': 'user', 'text': 'What is your main area of expertise?'}
            ]
        })
    }

    response = lambda_handler(test_event, None)
    print("\n=== Test Response ===")
    print(json.dumps(json.loads(response['body']), indent=2))
