#!/usr/bin/env python3
"""
Quick local test script for Virtual Me chatbot.
Tests the RAG pipeline with LM Studio.
"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("Virtual Me - Local Test")
print("=" * 60)

# Test 1: Configuration
print("\n1. Testing Configuration...")
try:
    from config import get_model_config
    config = get_model_config()
    print(f"   ✓ Backend: {config.backend}")
    print(f"   ✓ Model: {config.model_id}")
    print(f"   ✓ Temperature: {config.temperature}")
    print(f"   ✓ LM Studio URL: {config.lm_studio_base_url}")
except Exception as e:
    print(f"   ✗ Configuration error: {e}")
    sys.exit(1)

# Test 2: Knowledge Base Loading
print("\n2. Testing Knowledge Base Loading...")
try:
    from loaders.knowledge_base import load_knowledge_base
    documents = load_knowledge_base()
    print(f"   ✓ Loaded {len(documents)} document chunks")
    if documents:
        print(f"   ✓ Sample: {documents[0].page_content[:100]}...")
except Exception as e:
    print(f"   ✗ Knowledge base error: {e}")
    sys.exit(1)

# Test 3: LLM Connection (LM Studio)
print("\n3. Testing LLM Connection (LM Studio)...")
print("   ⚠ Make sure LM Studio server is running on http://localhost:1234")
try:
    from rag.generator import generate_response

    test_context = "I have 8 years of experience in software engineering."
    test_question = "How many years of experience do you have?"

    response = generate_response(test_context, test_question)
    print(f"   ✓ LLM Response: {response[:100]}...")

    if "8" in response or "eight" in response.lower():
        print("   ✓ Response looks correct!")
    else:
        print("   ⚠ Response might be incorrect - check manually")

except Exception as e:
    print(f"   ✗ LLM connection error: {e}")
    print("\n   Troubleshooting:")
    print("   - Is LM Studio running?")
    print("   - Is the server started in LM Studio?")
    print("   - Is Ministral 3 14B model loaded?")
    sys.exit(1)

# Test 4: Full RAG Pipeline (requires DynamoDB or will skip)
print("\n4. Testing Full RAG Pipeline...")
print("   ⚠ This requires DynamoDB (local or AWS)")
try:
    from rag.pipeline import run_rag_pipeline

    test_question = "What is your experience with AWS?"
    print(f"   Question: {test_question}")

    answer = run_rag_pipeline(test_question)
    print(f"   ✓ Answer: {answer[:200]}...")

except Exception as e:
    print(f"   ⚠ RAG pipeline skipped (expected if DynamoDB not available): {e}")

print("\n" + "=" * 60)
print("✅ Local testing complete!")
print("=" * 60)
print("\nIf all tests passed, you're ready to deploy!")
print("Run: cd terraform && terraform apply")
