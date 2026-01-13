"""Unit tests for knowledge base loader."""

from loaders.knowledge_base import load_knowledge_base


def test_load_knowledge_base():
    """Test that knowledge base loads successfully."""
    documents = load_knowledge_base()

    assert isinstance(documents, list)
    assert len(documents) > 0

    # Check first document structure
    first_doc = documents[0]
    assert hasattr(first_doc, 'page_content')
    assert hasattr(first_doc, 'metadata')

    print(f"✓ Loaded {len(documents)} documents")


def test_documents_have_metadata():
    """Test that documents have header metadata."""
    documents = load_knowledge_base()

    # At least some documents should have header metadata
    docs_with_headers = [
        doc for doc in documents
        if 'Header 1' in doc.metadata or 'Header 2' in doc.metadata
    ]

    assert len(docs_with_headers) > 0
    print(f"✓ {len(docs_with_headers)} documents have header metadata")


def test_documents_have_content():
    """Test that documents have non-empty content."""
    documents = load_knowledge_base()

    for doc in documents:
        assert len(doc.page_content) > 0

    print("✓ All documents have content")


if __name__ == '__main__':
    print("Running knowledge base loader tests...")
    test_load_knowledge_base()
    test_documents_have_metadata()
    test_documents_have_content()
    print("✓ All tests passed!")
