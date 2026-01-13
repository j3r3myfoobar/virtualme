"""Unit tests for validation utilities."""

import pytest

from utils.validation import validate_not_empty_whitespace, validate_no_null_bytes


class TestValidateNotEmptyWhitespace:
    """Tests for validate_not_empty_whitespace."""

    def test_valid_text_returns_stripped(self):
        """Test valid text with whitespace is stripped and returned."""
        result = validate_not_empty_whitespace("  hello world  ")
        assert result == "hello world"

    def test_valid_text_no_strip(self):
        """Test valid text with strip=False returns original."""
        result = validate_not_empty_whitespace("  hello  ", strip=False)
        assert result == "  hello  "

    def test_empty_string_raises(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            validate_not_empty_whitespace("")

    def test_whitespace_only_raises(self):
        """Test whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            validate_not_empty_whitespace("   \t\n  ")

    def test_single_character(self):
        """Test single character is valid."""
        result = validate_not_empty_whitespace("a")
        assert result == "a"

    def test_unicode_text(self):
        """Test unicode text is handled correctly."""
        result = validate_not_empty_whitespace("  Bonjour!")
        assert result == "Bonjour!"


class TestValidateNoNullBytes:
    """Tests for validate_no_null_bytes."""

    def test_valid_text_passes(self):
        """Test text without null bytes passes."""
        result = validate_no_null_bytes("hello world")
        assert result == "hello world"

    def test_null_byte_raises(self):
        """Test null byte in text raises ValueError."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_no_null_bytes("hello\x00world")

    def test_null_byte_at_start(self):
        """Test null byte at start raises ValueError."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_no_null_bytes("\x00hello")

    def test_null_byte_at_end(self):
        """Test null byte at end raises ValueError."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_no_null_bytes("hello\x00")

    def test_empty_string_passes(self):
        """Test empty string passes (no null bytes)."""
        result = validate_no_null_bytes("")
        assert result == ""

    def test_special_characters_pass(self):
        """Test other special characters pass."""
        result = validate_no_null_bytes("hello\n\t\rworld")
        assert result == "hello\n\t\rworld"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
