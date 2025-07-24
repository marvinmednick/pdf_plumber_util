"""
Dynamic README.md transformation script for mkdocs-gen-files.

This script reads the original README.md from the project root and transforms
the links to work correctly in the mkdocs documentation site context.

Link Transformations:
- docs/cli-usage.md → cli-usage.md
- docs/architecture.md → architecture.md  
- docs/design-decisions.md → design-decisions.md
- CLAUDE.md → development.md

This preserves the original README.md for repository viewers while generating
a docs-friendly version for the mkdocs site.
"""

import mkdocs_gen_files
from pathlib import Path

def transform_readme_links(content: str) -> str:
    """
    Transform README.md links for mkdocs context.
    
    Args:
        content: Original README.md content
        
    Returns:
        Content with transformed links for docs site
    """
    # Link mappings for docs context
    link_mappings = {
        "docs/cli-usage.md": "cli-usage.md",
        "docs/architecture.md": "architecture.md", 
        "docs/design-decisions.md": "design-decisions.md",
        "CLAUDE.md": "development.md"
    }
    
    # Apply transformations
    for original, replacement in link_mappings.items():
        content = content.replace(original, replacement)
    
    return content

# Read original README.md from project root
readme_path = Path("README.md")
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    # Transform links for docs context
    transformed_content = transform_readme_links(original_content)
    
    # Write transformed version to docs site
    with mkdocs_gen_files.open("readme.md", "w") as f:
        f.write(transformed_content)