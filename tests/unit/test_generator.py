"""
Unit tests for LLM Response Generator.

Tests the generator functionality including response generation,
input validation, and LLM backend configuration.
"""

import pytest
from unittest.mock import MagicMock, patch

from rag.generator import generate_response, _get_llm, SYSTEM_PROMPT
from config import ModelConfig


class TestGenerateResponse:
    """Tests for generate_response function."""

    @patch('rag.generator._get_llm')
    def test_generate_response_returns_content(self, mock_get_llm, sample_context, sample_question):
        """generate_response should return LLM response content."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "I have 8 years of experience."
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = generate_response(sample_context, sample_question)

        assert result == "I have 8 years of experience."
        mock_llm.invoke.assert_called_once()

    def test_generate_response_empty_context_raises(self, sample_question):
        """generate_response should raise ValueError for empty context."""
        with pytest.raises(ValueError, match="Context cannot be empty"):
            generate_response("", sample_question)

    def test_generate_response_empty_question_raises(self, sample_context):
        """generate_response should raise ValueError for empty question."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            generate_response(sample_context, "")

    @patch('rag.generator._get_llm')
    def test_generate_response_uses_config(self, mock_get_llm, sample_context, sample_question):
        """generate_response should use provided config."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        config = ModelConfig(
            backend="bedrock",
            model_id="test-model",
            aws_region="us-east-1",
            temperature=0.5
        )

        generate_response(sample_context, sample_question, config)

        mock_get_llm.assert_called_once_with(config)

    @patch('rag.generator._get_llm')
    def test_generate_response_formats_prompt(self, mock_get_llm, sample_context, sample_question):
        """generate_response should format system prompt with context."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        generate_response(sample_context, sample_question)

        # Check that invoke was called with messages containing the context
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 2  # System prompt + question
        assert sample_context in call_args[0].content


class TestGetLLM:
    """Tests for _get_llm function."""

    def test_get_llm_bedrock_backend(self):
        """_get_llm should create ChatBedrock for bedrock backend."""
        mock_chat_bedrock = MagicMock()

        # Mock the langchain_aws module and ChatBedrock class
        mock_langchain_aws = MagicMock()
        mock_langchain_aws.ChatBedrock = mock_chat_bedrock

        with patch.dict('sys.modules', {'langchain_aws': mock_langchain_aws}):
            # Need to reload the module to pick up the mock
            config = ModelConfig(
                backend="bedrock",
                model_id="anthropic.claude-v2",
                aws_region="us-east-1",
                temperature=0.1
            )

            _get_llm(config)

            mock_chat_bedrock.assert_called_once()
            call_kwargs = mock_chat_bedrock.call_args[1]
            assert call_kwargs['model_id'] == "anthropic.claude-v2"
            assert call_kwargs['region_name'] == "us-east-1"

    def test_get_llm_unsupported_backend_raises(self):
        """ModelConfig should raise ValidationError for unsupported backend."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Input should be 'bedrock' or 'lm_studio'"):
            ModelConfig(
                backend="unsupported",
                model_id="test-model",
                aws_region="us-east-1",
                temperature=0.1
            )


class TestSystemPrompt:
    """Tests for system prompt configuration."""

    def test_system_prompt_contains_context_placeholder(self):
        """System prompt should contain {context} placeholder."""
        assert "{context}" in SYSTEM_PROMPT

    def test_system_prompt_contains_critical_rules(self):
        """System prompt should contain critical rules for hallucination prevention."""
        assert "CRITICAL RULES" in SYSTEM_PROMPT
        assert "CONTEXT" in SYSTEM_PROMPT

    def test_system_prompt_can_be_formatted(self, sample_context):
        """System prompt should be formattable with context."""
        formatted = SYSTEM_PROMPT.format(context=sample_context)
        assert sample_context in formatted
        assert "{context}" not in formatted
