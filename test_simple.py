#!/usr/bin/env python3
"""
Simple local test - Tests basic functionality without complex imports.
"""

import sys
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("Virtual Me - Simple Local Test")
print("=" * 60)

# Test 1: Environment Variables
print("\n1. Checking Environment Variables...")
backend = os.environ.get('LLM_BACKEND', 'not set')
model = os.environ.get('LLM_MODEL', 'not set')
temp = os.environ.get('LLM_TEMPERATURE', 'not set')

print(f"   LLM_BACKEND: {backend}")
print(f"   LLM_MODEL: {model}")
print(f"   LLM_TEMPERATURE: {temp}")

if backend == 'lm_studio' and model == 'ministral-3-14b-instruct-2512' and temp == '0.1':
    print("   ✓ Environment configured correctly!")
else:
    print("   ⚠ Check your .env file")

# Test 2: Python Syntax Check
print("\n2. Checking Python Syntax...")
files_to_check = [
    'src/config.py',
    'src/rag/generator.py',
    'src/rag/pipeline.py',
    'terraform/variables.tf'
]

all_good = True
for file_path in files_to_check:
    if file_path.endswith('.py'):
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"   ✓ {file_path}")
        except SyntaxError as e:
            print(f"   ✗ {file_path}: {e}")
            all_good = False
    else:
        # Just check file exists
        if os.path.exists(file_path):
            print(f"   ✓ {file_path} exists")
        else:
            print(f"   ✗ {file_path} not found")

# Test 3: Test LM Studio Connection
print("\n3. Testing LM Studio Connection...")
print("   Attempting to connect to http://localhost:1234...")

try:
    import requests
    response = requests.get('http://localhost:1234/v1/models', timeout=2)
    if response.status_code == 200:
        print("   ✓ LM Studio server is running!")
        models = response.json()
        print(f"   ✓ Available models: {models}")
    else:
        print(f"   ⚠ LM Studio responded with status: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ✗ Cannot connect to LM Studio")
    print("   Make sure LM Studio is running with server started")
except ImportError:
    print("   ⚠ requests library not available, skipping connection test")
except Exception as e:
    print(f"   ⚠ Connection test failed: {e}")

# Test 4: Resume file
print("\n4. Checking Resume File...")
resume_path = 'src/resume.md'
if os.path.exists(resume_path):
    with open(resume_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        print(f"   ✓ Resume found: {len(lines)} lines")
        # Check for the Lambda optimization mention
        if '3 seconds to under 500ms' in content:
            print("   ✓ Lambda optimization mentioned")
        if '60%' in content:
            print("   ✓ Cost reduction metric found")
        if 'Tech Innovations Inc' in content:
            print("   ✓ Company name found")
else:
    print(f"   ✗ Resume not found at {resume_path}")

print("\n" + "=" * 60)
print("✅ Basic checks complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Make sure LM Studio is running with Ministral 3 14B loaded")
print("2. Run: cd terraform && terraform plan")
print("3. If plan looks good: terraform apply")
