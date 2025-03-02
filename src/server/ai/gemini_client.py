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

class SelectIssuesResponse(BaseModel):
    beginner_issues: list[int]
    intermediate_issues: list[int]
    advanced_issues: list[int]

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)

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

    def generate_crazy_idea(self, repo_name: str, content: str) -> str:
        """
        Generate a creative and innovative feature idea for a GitHub project.

        Parameters
        ----------
        repo_name : str
            Name of the repository
        content : str
            Content/description of the repository

        Returns
        -------
        str
            A creative feature idea for the project
        """
        prompt = f"Generate 1 creative and innovative feature idea for the GitHub project '{repo_name}' which is described as: '{content}'. Make the idea 1-2 sentences long. Your response should only contain plain text without any symbols, special characters, or formatting elements."

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "text/plain",
                },
            )

            if response and response.text:
                return response.text

            return "Error generating crazy idea"
        except Exception as e:
            print(f"Error generating crazy idea: {e}")
            return "Error generating crazy idea"

    def select_issues(self, issues: list, repo_name: str, content: str) -> SelectIssuesResponse:
        """
        Analyze and select the most relevant issues from a repository.

        Parameters
        ----------
        issues : list
            List of issues from the repository
        repo_name : str
            Name of the repository
        content : str
            Content/description of the repository

        Returns
        -------
        SelectIssuesResponse
            Object containing categorized issues (beginner, intermediate, advanced)
        """

        # Create the prompt for Gemini
        prompt = f"""
        Given these issues from the GitHub repository '{repo_name}':
        {json.dumps(issues, indent=2)}

        And this repository description:
        {content[:1000]}  # Limit content length

        Categorize the issues into three categories:
        1. Beginner issues: Issues suitable for newcomers to the project
        2. Intermediate issues: Issues requiring moderate familiarity with the project
        3. Advanced issues: Issues requiring deep understanding of the project

        For each category, select up to 3 of the most relevant issues and return their indices from the original list.

        Format the response as JSON with keys: 'beginner_issues', 'intermediate_issues', 'advanced_issues'
        Each key should contain an array of integers representing the indices of the selected issues in the original list.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[SelectIssuesResponse],
                },
            )

            if response and response.candidates:
                # Extract the parsed response
                return json.loads(response.text)[0]

            return {
                "beginner_issues": [],
                "intermediate_issues": [],
                "advanced_issues": []
            }

        except Exception as e:
            print(f"Error selecting issues: {e}")
            return {
                "beginner_issues": [],
                "intermediate_issues": [],
                "advanced_issues": []
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
