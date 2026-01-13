"""
Unit tests for DynamoDB Vector Store.

Tests the vector store functionality including ID generation,
cosine similarity, and binary embedding conversion.
"""

import pytest
from unittest.mock import MagicMock, patch

from vectorstores.dynamodb_vector_store import DynamoDBVectorStore


class TestDocIdGeneration:
    """Tests for deterministic document ID generation."""

    def test_generate_doc_id_deterministic(self):
        """Same text and index should always produce same ID."""
        text = "Hello World"
        id1 = DynamoDBVectorStore._generate_doc_id(text, 0)
        id2 = DynamoDBVectorStore._generate_doc_id(text, 0)
        assert id1 == id2

    def test_generate_doc_id_different_texts(self):
        """Different texts should produce different IDs."""
        id1 = DynamoDBVectorStore._generate_doc_id("Hello World", 0)
        id2 = DynamoDBVectorStore._generate_doc_id("Goodbye World", 0)
        assert id1 != id2

    def test_generate_doc_id_different_indices(self):
        """Same text with different indices should produce different IDs."""
        text = "Hello World"
        id1 = DynamoDBVectorStore._generate_doc_id(text, 0)
        id2 = DynamoDBVectorStore._generate_doc_id(text, 1)
        assert id1 != id2

    def test_generate_doc_id_format(self):
        """ID should have correct format: doc_{index}_{hash}."""
        doc_id = DynamoDBVectorStore._generate_doc_id("Test", 5)
        assert doc_id.startswith("doc_5_")
        assert len(doc_id) == len("doc_5_") + 12  # 12 hex chars from SHA256


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity of 1.0."""
        vec = [1.0, 2.0, 3.0]
        similarity = DynamoDBVectorStore._cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, rel=1e-5)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity of 0.0."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = DynamoDBVectorStore._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, rel=1e-5)

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity of -1.0."""
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        similarity = DynamoDBVectorStore._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0, rel=1e-5)

    def test_zero_vector(self):
        """Zero vector should return 0.0 similarity."""
        vec1 = [0.0, 0.0]
        vec2 = [1.0, 2.0]
        similarity = DynamoDBVectorStore._cosine_similarity(vec1, vec2)
        assert similarity == 0.0


class TestEmbeddingBinaryConversion:
    """Tests for embedding to/from binary conversion."""

    def test_roundtrip_conversion(self):
        """Embedding should survive binary roundtrip."""
        original = [1.5, 2.5, 3.5, 4.5]
        binary = DynamoDBVectorStore._embedding_to_binary(original)
        recovered = DynamoDBVectorStore._binary_to_embedding(binary)
        assert recovered == pytest.approx(original, rel=1e-5)

    def test_empty_embedding(self):
        """Empty embedding should work."""
        original = []
        binary = DynamoDBVectorStore._embedding_to_binary(original)
        recovered = DynamoDBVectorStore._binary_to_embedding(binary)
        assert recovered == []

    def test_single_value(self):
        """Single value embedding should work."""
        original = [3.14159]
        binary = DynamoDBVectorStore._embedding_to_binary(original)
        recovered = DynamoDBVectorStore._binary_to_embedding(binary)
        assert recovered == pytest.approx(original, rel=1e-5)


class TestVectorStoreOperations:
    """Tests for vector store operations with mocked DynamoDB."""

    @patch('vectorstores.dynamodb_vector_store.boto3')
    def test_add_documents_calls_batch_writer(self, mock_boto3):
        """add_documents should use batch_writer for efficiency."""
        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=None)
        mock_boto3.resource.return_value.Table.return_value = mock_table

        store = DynamoDBVectorStore("test-table", "us-east-1")
        texts = ["doc1", "doc2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        store.add_documents(texts, embeddings)

        mock_table.batch_writer.assert_called_once()
        assert mock_batch.put_item.call_count == 2

    @patch('vectorstores.dynamodb_vector_store.boto3')
    def test_similarity_search_returns_top_k(self, mock_boto3):
        """similarity_search should return top k results."""
        mock_table = MagicMock()

        # Create mock items with binary embeddings
        # Note: Cosine similarity measures direction, not magnitude
        # So we need vectors pointing in different directions
        items = []
        texts = ["low similarity", "high similarity", "medium similarity"]
        embeddings = [
            [0.0, 1.0, 0.0],  # Orthogonal to query - low similarity
            [1.0, 0.0, 0.0],  # Same direction as query - high similarity
            [0.7, 0.7, 0.0],  # Partially aligned - medium similarity
        ]

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            binary_emb = MagicMock()
            binary_emb.value = DynamoDBVectorStore._embedding_to_binary(emb)
            items.append({
                'id': f'doc_{i}',
                'text': text,
                'embedding': binary_emb,
                'metadata': '{}'
            })

        mock_table.scan.return_value = {'Items': items}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        store = DynamoDBVectorStore("test-table", "us-east-1")
        query_embedding = [1.0, 0.0, 0.0]  # Should match "high similarity" best

        results = store.similarity_search(query_embedding, k=2)

        assert len(results) == 2
        assert results[0][0] == "high similarity"  # Highest similarity first

    @patch('vectorstores.dynamodb_vector_store.boto3')
    def test_count_returns_item_count(self, mock_boto3):
        """count should return number of items in table."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {'Count': 42}
        mock_boto3.resource.return_value.Table.return_value = mock_table

        store = DynamoDBVectorStore("test-table", "us-east-1")
        count = store.count()

        assert count == 42
        mock_table.scan.assert_called_once_with(Select='COUNT')
