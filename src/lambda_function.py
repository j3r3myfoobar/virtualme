"""
Virtual Me Chatbot - AWS Lambda Handler

Main entry point for the Lambda function. Delegates to the RAG pipeline.
"""

import json
from typing import Dict, Any
from pydantic import ValidationError

from rag.pipeline import run_rag_pipeline
from utils.http import http_response
from models.requests import ChatRequest, ErrorResponse


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main AWS Lambda handler function.

    Processes POST requests from Deep Chat frontend with conversation history.
    Extracts the latest user message and runs it through the RAG pipeline.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        HTTP response with AI-generated answer

    Example event:
        {
            'body': '{"messages": [{"role": "user", "text": "Hello"}]}',
            'requestContext': {'http': {'method': 'POST'}}
        }
    """

    # Handle CORS preflight requests
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return http_response(200, {'message': 'OK'})

    try:
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))

        # Validate request with Pydantic
        try:
            chat_request = ChatRequest(**body)
        except ValidationError as e:
            # Return detailed validation errors
            error_response = ErrorResponse(
                error="Invalid request format",
                details=e.errors()
            )
            return http_response(422, error_response.model_dump())

        # Extract the last user message (already validated by Pydantic)
        last_user_message = chat_request.messages[-1].text

        print(f"Processing question: {last_user_message[:100]}...")

        # Run the RAG pipeline
        answer = run_rag_pipeline(last_user_message)

        print(f"Generated answer ({len(answer)} chars)")

        # Format response for Deep Chat
        response_body = {
            'text': answer
        }

        return http_response(200, response_body)

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return http_response(400, {'error': 'Invalid JSON in request body'})

    except ValueError as e:
        # Validation errors (empty question, missing API key, etc.)
        print(f"Validation error: {e}")
        return http_response(400, {'error': str(e)})

    except Exception as e:
        # Unexpected errors - log details internally but don't expose to client
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

        return http_response(500, {
            'error': 'Internal server error'
        })


# ============================================================================
# LOCAL TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Local testing script. Set OPENAI_API_KEY environment variable before running.

    Usage:
        export OPENAI_API_KEY="sk-proj-xxx"
        cd src
        python lambda_function.py
    """
    print("=" * 60)
    print("Virtual Me Chatbot - Local Test")
    print("=" * 60)

    # Mock event for testing
    test_event = {
        'body': json.dumps({
            'messages': [
                {'role': 'user', 'text': 'What is your main area of expertise?'}
            ]
        }),
        'requestContext': {
            'http': {'method': 'POST'}
        }
    }

    print("\nProcessing test request...")
    response = lambda_handler(test_event, None)

    print("\n" + "=" * 60)
    print("Test Response")
    print("=" * 60)
    print(f"Status Code: {response['statusCode']}")
    print(f"\nBody:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print("=" * 60)
