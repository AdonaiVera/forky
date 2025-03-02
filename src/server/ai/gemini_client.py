import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()


class AnalyzeRepositoryResponse(BaseModel):
    summary: str
    use_cases: list[str]
    contribution_insights: list[str]


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)

    async def generate_content(self, prompt: str) -> str | None:
        try:
            #response = await self.client.generate_content_async(prompt)
            #return response.text.strip()
            return "test"
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            return None

    def analyze_repository(
        self, tree_structure: str, repo_description: str
    ) -> dict[str, Any]:
        """
        Analyze a repository and generate insights using Gemini.

        Parameters
        ----------
        tree_structure : str
            The directory tree structure of the repository
        repo_description : str
            Description of the repository

        Returns
        -------
        Dict[str, Any]
            JSON containing summary, use cases, and contribution insights
        """
        prompt = f"""
        Given this repository structure:
        {tree_structure}

        And this repository description:
        {repo_description}

        Please provide:
        1. A brief summary of the repository (max 100 words)
        2. Three specific use cases for this project
        3. Three specific areas that you can learn if you contribute to this project

        Format the response as JSON with keys: 'summary', 'use_cases', 'contribution_insights'
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[AnalyzeRepositoryResponse],
                },
            )

            if response and response.candidates:
                # Extract the first candidate's parsed response
                return json.loads(response.text)[0]

            return {
                "summary": "Error generating repository analysis",
                "use_cases": [],
                "contribution_insights": []
            }
        except Exception as e:
            print(f"Error analyzing repository: {e}")
            return {
                "summary": "Error analyzing repository",
                "use_cases": [],
                "contribution_insights": []
            }

    def get_installation_instructions(self, readme: str) -> str:
        """
        Extract installation instructions from repository description.

        Parameters
        ----------
        repo_description : str
            Description of the repository containing installation steps

        Returns
        -------
        str
            Terminal commands for installing and running the project
        """
        prompt = f"""
        Given this repository description:
        {readme}

        Extract ONLY the terminal commands needed to clone, install, and run the project.

        Format your response as a step-by-step guide with code blocks:
        ```bash
        # Step 1: Clone the repository
        git clone [repository-url]
        cd [repository-name]

        # Step 2: Install dependencies
        [install command]

        # Step 3: Run the project
        [run command]
        ```

        Add all the ways to do it.
        If specific commands aren't found in the README, provide the most appropriate commands based on the project type (Python, JavaScript, etc.).
        Include ONLY terminal commands with brief comments - no explanatory text.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            if response and response.text:
                # Return the commands directly
                return response.text.strip()

            return "# No installation instructions found\npip install ."

        except Exception as e:
            print(f"Error getting installation instructions: {e}")
            return "# Error retrieving installation instructions"

    async def chat(self, message: str) -> str:
        """
        Process a chat message and return a simple acknowledgment.

        Parameters
        ----------
        message : str
            The message received from the user

        Returns
        -------
        str
            A simple acknowledgment message
        """
        try:
            return f"I received: {message}"
        except Exception as e:
            print(f"Error in chat: {e}")
            return "Sorry, there was an error processing your message."
