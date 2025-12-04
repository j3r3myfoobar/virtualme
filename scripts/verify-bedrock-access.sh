#!/bin/bash
###############################################################################
# Verify Bedrock Access in eu-west-3
# Tests both Llama 3.2 3B (EU inference profile) and Titan Embeddings
###############################################################################

set -e

REGION="eu-west-3"
LLAMA_MODEL="eu.meta.llama3-2-3b-instruct-v1:0"
TITAN_MODEL="amazon.titan-embed-text-v2:0"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Verifying Bedrock Access in eu-west-3                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# 1. Check AWS credentials
echo "1️⃣  Checking AWS credentials..."
ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ Authenticated as account: $ACCOUNT"
else
    echo "   ❌ AWS credentials not configured"
    exit 1
fi
echo

# 2. List EU inference profiles
echo "2️⃣  Checking EU Inference Profiles..."
PROFILES=$(aws bedrock list-inference-profiles \
    --region "$REGION" \
    --query 'inferenceProfileSummaries[?contains(inferenceProfileName, `Llama`)].inferenceProfileId' \
    --output text 2>/dev/null)

if [ -z "$PROFILES" ]; then
    echo "   ❌ No Llama inference profiles found"
    exit 1
else
    echo "   ✅ Found EU Llama inference profiles:"
    aws bedrock list-inference-profiles \
        --region "$REGION" \
        --query 'inferenceProfileSummaries[?contains(inferenceProfileName, `Llama`)].{Name:inferenceProfileName, Id:inferenceProfileId, Status:status}' \
        --output table
fi
echo

# 3. Test Llama 3.2 3B
echo "3️⃣  Testing Llama 3.2 3B model..."
LLM_OUTPUT=$(mktemp)
aws bedrock-runtime invoke-model \
    --region "$REGION" \
    --model-id "$LLAMA_MODEL" \
    --body '{"prompt":"Say hello in one word","max_gen_len":5,"temperature":0.1}' \
    --cli-binary-format raw-in-base64-out \
    "$LLM_OUTPUT" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Llama 3.2 3B is accessible"
    echo "   Response: $(cat "$LLM_OUTPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['generation'][:50])")"
    echo "   Model ID: $LLAMA_MODEL"
else
    echo "   ❌ Cannot invoke Llama 3.2 3B"
    echo "   You may need to request model access in Bedrock console"
    exit 1
fi
rm "$LLM_OUTPUT"
echo

# 4. Test Titan Embeddings
echo "4️⃣  Testing Titan Embeddings..."
EMBED_OUTPUT=$(mktemp)
aws bedrock-runtime invoke-model \
    --region "$REGION" \
    --model-id "$TITAN_MODEL" \
    --body '{"inputText":"Test embedding"}' \
    --cli-binary-format raw-in-base64-out \
    "$EMBED_OUTPUT" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    EMBED_DIM=$(cat "$EMBED_OUTPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d['embedding']))")
    echo "   ✅ Titan Embeddings is accessible"
    echo "   Embedding dimension: $EMBED_DIM"
    echo "   Model ID: $TITAN_MODEL"
else
    echo "   ❌ Cannot invoke Titan Embeddings"
    echo "   You may need to request model access in Bedrock console"
    exit 1
fi
rm "$EMBED_OUTPUT"
echo

# 5. Check foundation models
echo "5️⃣  Available foundation models in eu-west-3:"
aws bedrock list-foundation-models \
    --region "$REGION" \
    --query 'modelSummaries[?contains(modelId, `llama`) || contains(modelId, `titan-embed`)].{ModelId:modelId, Provider:providerName}' \
    --output table
echo

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ All Bedrock checks passed!                                 ║"
echo "║                                                                ║"
echo "║  You're ready to deploy to eu-west-3:                         ║"
echo "║  cd terraform && terraform init && terraform apply             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
