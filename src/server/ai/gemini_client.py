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
    contribution_insights: str


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)

    async def generate_content(self, prompt: str) -> str | None:
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
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
        3. Why someone should contribute, including required skills and areas of expertise

        Format the response as JSON with keys: 'summary', 'use_cases', 'contribution_insights'
        """

        print(prompt)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[AnalyzeRepositoryResponse],
                },
            )

            print("--------------------------------")
            print(response.text)
            print(type(response.text))
            print("--------------------------------")

            if response:
                return json.loads(response)
            return {
                "summary": "Error generating repository analysis",
                "use_cases": [],
                "contribution_insights": {},
            }
        except Exception as e:
            print(f"Error analyzing repository: {e}")
            return {
                "summary": "Error analyzing repository",
                "use_cases": [],
                "contribution_insights": {},
            }

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
