import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool
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

class RepositorySearchResponse(BaseModel):
    repo_full_name: str
    description: str
    language: str
    match_reason: str

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)
        self.chat_histories = {}  # Store chat histories by session ID


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

    async def chat(self, message: str, summary: str = "", content: str = "", session_id: str = None) -> str:
        """
        Process a chat message and generate a response using Gemini.

        Parameters
        ----------
        message : str
            The message received from the user
        summary : str
            Summary of the repository
        content : str
            Content/context from the repository
        session_id : str
            Unique identifier for the chat session

        Returns
        -------
        str
            AI-generated response based on the context
        """
        try:
            # Initialize or get existing chat history
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = []

            # Add user message to history
            self.chat_histories[session_id].append({
                "role": "user",
                "content": message
            })

            # Create a prompt that includes repository context and chat history
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.chat_histories[session_id][-5:]  # Include last 5 messages
            ])

            prompt = f"""
            You are a friendly and helpful AI assistant chatting with a user about a code repository.

            Repository context:
            Summary: {summary}
            Content: {content}

            Chat history:
            {history_text}

            The user says: "{message}"

            Respond in a conversational, friendly tone while:
            - Addressing their question or comment directly
            - Drawing from the repository context when relevant
            - Using specific code examples or references where helpful
            - Being encouraging and supportive
            - Using natural language and occasional emojis
            - Keeping responses concise but informative

            Remember to maintain a helpful and engaging conversation.
            """

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "text/plain",
                },
            )

            if response and response.text:
                response_text = response.text.strip()
                # Add assistant response to history
                self.chat_histories[session_id].append({
                    "role": "assistant",
                    "content": response_text
                })
                return response_text

            return "I'm having trouble understanding that. Could you rephrase your question? 🤔"

        except Exception as e:
            print(f"Error in chat: {e}")
            return "Oops! Something went wrong on my end. Let's try that again! 😅"

    async def search_repositories_with_reasoning(self, query: str, temperature: float = 0.7) -> list:
        """
        Search for repositories using Gemini's knowledge with Google Search grounding.

        Parameters
        ----------
        query : str
            The search query from the user
        temperature : float, optional
            Controls the randomness of the model's responses. Higher values (e.g., 0.8) make the output more creative,
            while lower values (e.g., 0.2) make it more focused and deterministic. Default is 0.7.

        Returns
        -------
        list
            List of recommended repositories with reasons why they match
        """
        from google.genai.types import (GenerateContentConfig, GoogleSearch,
                                        Tool)

        # Configure Google Search as a tool
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )

        prompt = f"""
        Find the best GitHub repositories that match this search query: "{query}"

        For each repository, provide:
        1. The Repository name in the format "owner/repo"
        2. A brief description of what the repository is about
        3. The main programming language used
        4. A specific explanation of why this repository is a good match for the query

        Return your response as a JSON array with these fields for each repository:
        - "repo_full_name": The full name of the repository (e.g., "owner/repo")
        - "description": Brief description of the repository
        - "language": Main programming language
        - "match_reason": Specific reason why this repository matches the query

        Limit the response to the top 5 most relevant repositories.
        Make sure to include only real, existing GitHub repositories, the repo should be active and maintained, should have more than 5 files.

        Your response should be ONLY the JSON array, with no additional text or explanation.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"],
                    temperature=temperature,
                ),
            )

            if not response or not response.candidates:
                print("No response from Gemini")
                return []

            try:
                # Extract JSON from the response text
                response_text = response.text.strip()
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1

                if json_start == -1 or json_end == 0:
                    print("No JSON array found in response")
                    print(f"Raw response: {response_text}")
                    return []

                json_str = response_text[json_start:json_end]
                repositories = json.loads(json_str)

                if not isinstance(repositories, list):
                    print(f"Unexpected response format: {json_str}")
                    return []

                return repositories

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response_text}")
                return []

        except Exception as e:
            print(f"Error searching repositories with reasoning: {e}")
            return []

    async def rank_repositories_by_readme(self, query: str, repositories: list) -> list:
        """
        Analyze READMEs of repositories and rank them based on relevance to the query.

        Parameters
        ----------
        query : str
            The original search query
        repositories : list
            List of repository objects with their metadata

        Returns
        -------
        list
            Top 3 repositories ranked by relevance to the query
        """
        prompt = f"""
        Given this search query: "{query}"

        And these repositories with their READMEs:
        {json.dumps(repositories, indent=2)}

        Analyze each repository's README and rank them based on how well they match the query.
        Consider:
        1. How well the repository's purpose aligns with the query
        2. The quality and completeness of the documentation
        3. The relevance of the features and functionality described

        Return your response as a JSON array with these fields for each repository:
        - "repo_full_name": The full name of the repository
        - "relevance_score": A number between 0 and 1 indicating how relevant the repo is to the query
        - "match_explanation": A brief explanation of why this repository is a good match

        Sort the repositories by relevance_score in descending order and return only the top 3.
        Your response should be ONLY the JSON array, with no additional text or explanation.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            if not response or not response.candidates:
                print("No response from Gemini for README analysis")
                return repositories[:3]  # Return first 3 if analysis fails

            try:
                # Extract JSON from the response text
                response_text = response.text.strip()
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1

                if json_start == -1 or json_end == 0:
                    print("No JSON array found in README analysis response")
                    return repositories[:3]

                json_str = response_text[json_start:json_end]
                ranked_repos = json.loads(json_str)

                if not isinstance(ranked_repos, list):
                    print(f"Unexpected README analysis response format: {json_str}")
                    return repositories[:3]

                # Create a mapping of repo names to their rankings
                repo_rankings = {
                    repo["repo_full_name"]: {
                        "relevance_score": repo["relevance_score"],
                        "match_explanation": repo["match_explanation"]
                    }
                    for repo in ranked_repos
                }

                # Sort original repositories based on rankings
                sorted_repos = sorted(
                    repositories,
                    key=lambda x: repo_rankings.get(x["full_name"], {}).get("relevance_score", 0),
                    reverse=True
                )

                # Add ranking information to the top 3 repositories
                for repo in sorted_repos[:3]:
                    ranking = repo_rankings.get(repo["full_name"], {})
                    repo["relevance_score"] = ranking.get("relevance_score", 0)
                    repo["match_explanation"] = ranking.get("match_explanation", "")

                return sorted_repos[:3]

            except json.JSONDecodeError as e:
                print(f"Error parsing README analysis JSON response: {e}")
                print(f"Raw response: {response_text}")
                return repositories[:3]

        except Exception as e:
            print(f"Error analyzing READMEs: {e}")
            return repositories[:3]
