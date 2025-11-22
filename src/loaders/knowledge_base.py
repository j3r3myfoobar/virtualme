"""
Knowledge base loader for Virtual Me chatbot.

Handles loading and splitting the resume.md file into chunks
while maintaining context hierarchy from markdown headers.
"""

import os
from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

# Import path setup
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


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
    # Get path to resume.md (same directory as this file's parent)
    resume_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'resume.md'
    )

    # Read the resume markdown file
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_content = f.read()

    # Define headers to split on - maintains context hierarchy
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    # Split the markdown maintaining header context
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )

    splits = markdown_splitter.split_text(resume_content)

    print(f"Loaded knowledge base: {len(splits)} chunks")

    return splits
