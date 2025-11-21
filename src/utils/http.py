"""
HTTP utilities for AWS Lambda API Gateway responses.
"""

import json
from typing import Dict, Any


def http_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format HTTP response with proper CORS headers for API Gateway.

    Args:
        status_code: HTTP status code (e.g., 200, 400, 500)
        body: Response body dictionary

    Returns:
        Formatted response dictionary for API Gateway

    Example:
        >>> http_response(200, {'text': 'Hello World'})
        {
            'statusCode': 200,
            'headers': {...},
            'body': '{"text": "Hello World"}'
        }
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
