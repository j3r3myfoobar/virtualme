"""Unit tests for HTTP utilities."""

import json

from utils.http import http_response


def test_http_response_success():
    """Test successful HTTP response formatting."""
    response = http_response(200, {'text': 'Hello World'})

    assert response['statusCode'] == 200
    assert 'headers' in response
    assert response['headers']['Content-Type'] == 'application/json'
    assert 'https://chat.lemaire.tel' in response['headers']['Access-Control-Allow-Origin']

    body = json.loads(response['body'])
    assert body['text'] == 'Hello World'


def test_http_response_error():
    """Test error HTTP response formatting."""
    response = http_response(500, {'error': 'Something went wrong'})

    assert response['statusCode'] == 500

    body = json.loads(response['body'])
    assert body['error'] == 'Something went wrong'


def test_http_response_cors_headers():
    """Test that CORS headers are present."""
    response = http_response(200, {})

    headers = response['headers']
    assert 'Access-Control-Allow-Origin' in headers
    assert 'Access-Control-Allow-Headers' in headers
    assert 'Access-Control-Allow-Methods' in headers


if __name__ == '__main__':
    print("Running HTTP utility tests...")
    test_http_response_success()
    test_http_response_error()
    test_http_response_cors_headers()
    print("✓ All tests passed!")
