#!/usr/bin/env python
"""Run all unit tests."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Import test modules
from unit import test_http
from unit import test_knowledge_base
from unit import test_lambda_handler


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("Running All Unit Tests")
    print("=" * 60)

    tests = [
        ("HTTP Utilities", [
            test_http.test_http_response_success,
            test_http.test_http_response_error,
            test_http.test_http_response_cors_headers,
        ]),
        ("Knowledge Base Loader", [
            test_knowledge_base.test_load_knowledge_base,
            test_knowledge_base.test_documents_have_metadata,
            test_knowledge_base.test_documents_have_content,
        ]),
        ("Lambda Handler", [
            test_lambda_handler.test_extract_last_user_message,
            test_lambda_handler.test_extract_last_user_message_empty,
            test_lambda_handler.test_extract_last_user_message_whitespace,
        ]),
    ]

    total_tests = 0
    passed_tests = 0

    for suite_name, test_functions in tests:
        print(f"\n{suite_name}")
        print("-" * 60)

        for test_func in test_functions:
            total_tests += 1
            try:
                test_func()
                print(f"  ✓ {test_func.__name__}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ✗ {test_func.__name__}: {e}")
            except Exception as e:
                print(f"  ✗ {test_func.__name__}: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    return passed_tests == total_tests


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
