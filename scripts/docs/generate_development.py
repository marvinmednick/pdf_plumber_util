"""
Dynamic CLAUDE.md transformation script for mkdocs-gen-files.

This script reads the original CLAUDE.md from the project root and transforms
the internal documentation links to work correctly in the mkdocs documentation 
site context.

Link Transformations:
- docs/test_docstring_guidelines.md → test_docstring_guidelines.md
- docs/architecture.md → architecture.md
- docs/design-decisions.md → design-decisions.md
- docs/phase-history.md → phase-history.md
- docs/status.md → status.md
- docs/design/*.md → design/*.md
- docs/analysis/*.md → analysis/*.md

This preserves the original CLAUDE.md for repository context while generating
a docs-friendly version for the mkdocs site.
"""

import mkdocs_gen_files
from pathlib import Path
import re

def transform_claude_links(content: str) -> str:
    """
    Transform CLAUDE.md links for mkdocs context.
    
    Args:
        content: Original CLAUDE.md content
        
    Returns:
        Content with transformed links for docs site
    """
    # Direct link mappings
    direct_mappings = {
        "docs/test_docstring_guidelines.md": "test_docstring_guidelines.md",
        "docs/architecture.md": "architecture.md",
        "docs/design-decisions.md": "design-decisions.md", 
        "docs/phase-history.md": "phase-history.md",
        "docs/status.md": "status.md",
        "docs/cli-usage.md": "cli-usage.md"
    }
    
    # Apply direct mappings
    for original, replacement in direct_mappings.items():
        content = content.replace(original, replacement)
    
    # Pattern-based transformations for design/ and analysis/ directories
    # Transform docs/design/*.md → design/*.md
    content = re.sub(r'docs/design/([^)]+\.md)', r'design/\1', content)
    
    # Transform docs/analysis/*.md → analysis/*.md
    content = re.sub(r'docs/analysis/([^)]+\.md)', r'analysis/\1', content)
    
    return content

# Read original CLAUDE.md from project root
claude_path = Path("CLAUDE.md")
if claude_path.exists():
    with open(claude_path, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    # Transform links for docs context
    transformed_content = transform_claude_links(original_content)
    
    # Write transformed version to docs site as development.md
    with mkdocs_gen_files.open("development.md", "w") as f:
        f.write(transformed_content)