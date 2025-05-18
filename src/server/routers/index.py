""" This module defines the FastAPI router for the home page of the application. """

import json
import os
import uuid

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Body, Cookie, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from server.ai.content_provider import gemini_client
from server.query_processor import process_query
from server.server_config import EXAMPLE_REPOS, templates
from server.server_utils import limiter

router = APIRouter()

# Load environment variables from .env file
load_dotenv()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Render the home page with example repositories and default parameters.

    This endpoint serves the home page of the application, rendering the `index.jinja` template
    and providing it with a list of example repositories and default file size values.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.

    Returns
    -------
    HTMLResponse
        An HTML response containing the rendered home page template, with example repositories
        and other default parameters such as file size.
    """
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "examples": EXAMPLE_REPOS,
            "default_file_size": 243,
        },
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index_post(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> HTMLResponse:
    """
    Process the form submission with user input for query parameters.

    This endpoint handles POST requests from the home page form. It processes the user-submitted
    input (e.g., text, file size, pattern type) and invokes the `process_query` function to handle
    the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    input_text : str
        The input text provided by the user for processing, by default taken from the form.
    max_file_size : int
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str
        The type of pattern used for the query, specified by the user.
    pattern : str
        The pattern string used in the query, specified by the user.

    Returns
    -------
    HTMLResponse
        An HTML response containing the results of processing the form input and query logic,
        which will be rendered and returned to the user.
    """
    return await process_query(
        request,
        input_text,
        max_file_size,
        pattern_type,
        pattern,
        is_index=True,
    )


@router.post("/chat", response_class=JSONResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    response: Response,
    message: str = Form(...),
    repo_summary: str = Form(None),
    repo_content: str = Form(None),
    session_id: str = Cookie(None)
) -> JSONResponse:
    """
    Handle chat messages and return AI responses.
    """
    try:
        # Generate session ID if not exists
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(key="session_id", value=session_id)

        # Use gemini_client for chat with repository context
        response_text = await gemini_client.chat(
            message,
            repo_summary,
            repo_content,
            session_id
        )

        # Return response with a flag indicating it contains markdown
        return JSONResponse(content={
            "response": str(response_text),
            "format": "markdown"  # Indicate this contains markdown formatting
        })
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@router.post("/search_repos", response_class=JSONResponse)
@limiter.limit("10/minute")
async def search_repos(
    request: Request,
    query: str = Form(...),
) -> JSONResponse:
    """
    Search GitHub repositories based on the provided query.

    This endpoint searches GitHub repositories that match the query and returns the top results,
    adding a 'good_fit' field determined using AI to indicate what type of contributors
    the repo would be good for.

    Parameters
    ----------
    request : Request
        The incoming request object
    query : str
        The search query to find repositories

    Returns
    -------
    JSONResponse
        A JSON response with the search results
    """
    try:
        # Get GitHub token from environment variables
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")

        headers = {"Authorization": f"token {github_token}"}

        # Get recommendations from Gemini with Google Search grounding
        recommended_repos = await gemini_client.search_repositories_with_reasoning(query)

        if not recommended_repos:
            return JSONResponse(content={"repos": []})

        result_repos = []

        # Fetch metadata and README for each recommended repository
        async with httpx.AsyncClient() as client:
            for repo in recommended_repos:
                try:
                    repo_full_name = repo.get("repo_full_name")
                    if not repo_full_name:
                        continue

                    # First search for repositories matching the query
                    search_url = f"https://api.github.com/search/repositories?q={repo_full_name}&sort=stars&order=desc"
                    search_response = await client.get(search_url, headers=headers, timeout=10.0)

                    if search_response.status_code != 200:
                        print(f"Error searching repositories: {search_response.status_code}")
                        continue

                    search_data = search_response.json()
                    if not search_data.get("items"):
                        continue

                    repo_metadata = search_data["items"][0]

                    # Fetch README content
                    readme_url = f"https://api.github.com/repos/{repo_full_name}/readme"
                    readme_response = await client.get(readme_url, headers=headers, timeout=10.0)
                    readme_content = ""

                    if readme_response.status_code == 200:
                        readme_data = readme_response.json()
                        if readme_data.get("content"):
                            import base64
                            readme_content = base64.b64decode(readme_data["content"]).decode('utf-8')

                    # Create enhanced repo object with metadata and README
                    enhanced_repo = {
                        "full_name": repo_metadata.get("full_name", ""),
                        "name": repo_metadata.get("name", ""),
                        "description": repo.get("description", ""),
                        "language": repo_metadata.get("language", ""),
                        "stars": repo_metadata.get("stargazers_count", 0),
                        "forks": repo_metadata.get("forks_count", 0),
                        "issues": repo_metadata.get("open_issues_count", 0),
                        "updated_at": repo_metadata.get("updated_at", ""),
                        "html_url": repo_metadata.get("html_url", ""),
                        "topics": repo_metadata.get("topics", []),
                        "good_fit": repo.get("match_reason", ""),
                        "readme": readme_content
                    }

                    result_repos.append(enhanced_repo)

                except Exception as e:
                    print(f"Error fetching metadata for repository {repo_full_name}: {e}")
                    continue

        # Rank repositories based on README content
        ranked_repos = await gemini_client.rank_repositories_by_readme(query, result_repos)

        return JSONResponse(content={"repos": ranked_repos})

    except Exception as e:
        print(f"Error in search_repos: {str(e)}")
        return JSONResponse(
            content={"error": f"Error searching repositories: {str(e)}"},
            status_code=500
        )
