OVERVIEW_DIAGRAM_PROMPT = """
Analyze this codebase structure and create a high-level Mermaid diagram showing the main components and their relationships.
Focus on the key modules and their interactions.

Directory structure:
{tree}

Return only the Mermaid diagram code starting with ```mermaid and ending with ```.
Use graph TD for the diagram.
Keep it simple with maximum 10 nodes.
Use appropriate Mermaid styling.
"""

DETAILED_DIAGRAM_PROMPT = """
Create a detailed Mermaid diagram showing the internal structure and relationships of this codebase.
Include important classes, functions, and their connections.

Directory structure:
{tree}

File contents (partial):
{content}

Return only the Mermaid diagram code starting with ```mermaid and ending with ```.
Use graph TD for the diagram.
Use subgraphs for modules.
Use appropriate Mermaid styling and icons.
"""
