"""Module for generating Mermaid diagrams from repository content."""

from server.ai.gemini_client import GeminiClient
from server.ai.prompts import DETAILED_DIAGRAM_PROMPT, OVERVIEW_DIAGRAM_PROMPT


class DiagramGenerator:
    """Generates overview and detailed Mermaid diagrams from repository content.

    Uses the Gemini AI model to generate diagrams representing repository structure
    and content relationships.
    """

    def __init__(self):
        """Initialize the DiagramGenerator with a GeminiClient instance."""
        self.client = GeminiClient()

    def is_ready(self) -> bool:
        """Check if the diagram generator is ready to generate diagrams.

        Returns:
            bool: True if the client is initialized and ready, False otherwise
        """
        return self.client is not None

    def _clean_mermaid_code(self, diagram: str | None) -> str:
        """Clean up the Mermaid diagram code.

        Args:
            diagram: Raw Mermaid diagram code that may contain markdown formatting

        Returns:
            Cleaned Mermaid diagram code with proper formatting and header
        """
        if not diagram:
            return self._generate_fallback_diagram("Error")

        # Remove markdown code block markers if present
        diagram = diagram.replace("```mermaid", "").replace("```", "").strip()

        # Ensure the diagram has the proper header
        if not diagram.startswith("graph TD"):
            diagram = "graph TD\n" + diagram

        return diagram

    def _generate_fallback_diagram(self, diagram_type: str) -> str:
        """Generate a fallback diagram if the main generation fails.

        Args:
            diagram_type: Type of diagram that failed to generate (e.g. "Error", "Overview")

        Returns:
            A simple Mermaid diagram indicating the generation failure
        """
        return f"""graph TD
        A[{diagram_type} Diagram] --> B[Diagram generation failed]
        B --> C[Please try again]
        style A fill:#f9f,stroke:#333,stroke-width:4px
        style B fill:#ff9,stroke:#333,stroke-width:2px
        style C fill:#9f9,stroke:#333,stroke-width:2px
        """

    async def generate_diagrams(self, tree: str, content: str) -> tuple[str, str]:
        """Generate both overview and detailed diagrams.

        Args:
            tree: Repository file tree structure
            content: Repository file contents

        Returns:
            A tuple containing (overview_diagram, detailed_diagram) as Mermaid diagram strings
        """
        # Generate overview diagram
        overview_prompt = OVERVIEW_DIAGRAM_PROMPT.format(tree=tree)
        overview_diagram = await self.client.generate_content(overview_prompt)
        overview_diagram = self._clean_mermaid_code(overview_diagram)

        # Generate detailed diagram
        detailed_prompt = DETAILED_DIAGRAM_PROMPT.format(
            tree=tree, content=content[:2000]  # Limit content length
        )
        detailed_diagram = await self.client.generate_content(detailed_prompt)
        detailed_diagram = self._clean_mermaid_code(detailed_diagram)

        return overview_diagram, detailed_diagram
