"""
Virtual Me Chatbot - AWS Lambda Handler

Main entry point for the Lambda function. Delegates to the RAG pipeline.
"""

import json
from typing import Dict, Any

from rag.pipeline import run_rag_pipeline
from utils.http import http_response
from utils.logger import get_logger, add_lambda_context

# Initialize structured logger
logger = get_logger(__name__)


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

    # Get Lambda context for logging
    context_data = add_lambda_context(context)

    # Handle CORS preflight requests
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        logger.debug("cors_preflight_request", **context_data)
        return http_response(200, {'message': 'OK'})

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        messages = body.get('messages', [])

        if not messages:
            logger.warning("no_messages_provided", **context_data)
            return http_response(400, {'error': 'No messages provided'})

        # Extract the last user message (Deep Chat sends full history)
        last_user_message = extract_last_user_message(messages)

        if not last_user_message:
            logger.warning("no_user_message_found",
                         message_count=len(messages),
                         **context_data)
            return http_response(400, {'error': 'No user message found'})

        # Log request
        logger.info("processing_question",
                   question_preview=last_user_message[:100],
                   question_length=len(last_user_message),
                   **context_data)

        # Run the RAG pipeline
        answer = run_rag_pipeline(last_user_message)

        # Format response for Deep Chat
        response_body = {
            'text': answer
        }

        # Log successful response
        logger.info("response_generated",
                   answer_preview=answer[:100],
                   answer_length=len(answer),
                   **context_data)

        return http_response(200, response_body)

    except json.JSONDecodeError as e:
        logger.error("invalid_json",
                    error=str(e),
                    **context_data)
        return http_response(400, {'error': 'Invalid JSON in request body'})

    except ValueError as e:
        # Validation errors (empty question, missing API key, etc.)
        logger.warning("validation_error",
                      error=str(e),
                      **context_data)
        return http_response(400, {'error': str(e)})

    except Exception as e:
        # Unexpected errors
        logger.error("unexpected_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                    **context_data)
        return http_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })


def extract_last_user_message(messages: list) -> str:
    """
    Extract the last user message from conversation history.

    Args:
        messages: List of message dictionaries with 'role' and 'text' keys

    Returns:
        Text of the last user message, or empty string if not found

    Example:
        >>> messages = [
        ...     {'role': 'user', 'text': 'Hello'},
        ...     {'role': 'ai', 'text': 'Hi there'},
        ...     {'role': 'user', 'text': 'How are you?'}
        ... ]
        >>> extract_last_user_message(messages)
        'How are you?'
    """
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            return msg.get('text', '').strip()
    return ''


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
