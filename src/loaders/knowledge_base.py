"""
Knowledge base loader for Virtual Me chatbot.

Handles loading and splitting the resume.md file into chunks
while maintaining context hierarchy from markdown headers.
"""

from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

from constants import RESUME_PATH, MARKDOWN_HEADERS_TO_SPLIT


def load_knowledge_base() -> List[Document]:
    """
    Load and split the resume.md file into document chunks.

    Uses MarkdownHeaderTextSplitter to maintain hierarchical context
    from markdown headers (#, ##, ###).

    Returns:
        List of Document objects with content and metadata

    Raises:
        FileNotFoundError: If resume.md is not found
        IOError: If file cannot be read

    Example:
        >>> docs = load_knowledge_base()
        >>> len(docs)
        15
        >>> docs[0].metadata
        {'Header 1': 'John Doe', 'Header 2': 'Experience'}
    """
    # Check if resume exists
    if not RESUME_PATH.exists():
        raise FileNotFoundError(
            f"Resume not found at {RESUME_PATH}. "
            f"Please ensure resume.md exists in the src directory."
        )

    # Read the resume markdown file
    try:
        resume_content = RESUME_PATH.read_text(encoding='utf-8')
    except IOError as e:
        raise IOError(f"Failed to read resume file: {e}")

    # Split the markdown maintaining header context
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MARKDOWN_HEADERS_TO_SPLIT,
        strip_headers=False
    )

    splits = markdown_splitter.split_text(resume_content)

    print(f"Loaded knowledge base: {len(splits)} chunks")

    return splits
