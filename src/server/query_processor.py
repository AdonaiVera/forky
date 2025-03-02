""" Process a query by parsing input and generating a summary using gitingest, google genai, and a custom AI agent. """

import asyncio
from functools import partial

import requests
from fastapi import Request
from gitingest import ingest_async
from starlette.templating import _TemplateResponse

from server.ai.content_provider import (get_general_overview_diagram,
                                        get_installation_usage,
                                        get_project_description,
                                        get_project_metrics,
                                        get_repository_issues)
from server.server_config import EXAMPLE_REPOS, MAX_DISPLAY_SIZE, templates
from server.server_utils import Colors, log_slider_to_size


async def handle_chat_message(message: str) -> str:
    """
    Process a chat message and return a response.

    Parameters
    ----------
    message : str
        The message received from the user.

    Returns
    -------
    str
        A response message.
    """
    # Example logic to generate a response
    response = f"Received your message: {message}"
    return response


async def process_query(
    request: Request,
    input_text: str,
    slider_position: int,
    pattern_type: str = "exclude",
    pattern: str = "",
    is_index: bool = False,
) -> _TemplateResponse:
    """
    Process a query by parsing input and generating a summary.

    Handle user input and prepare a response for rendering a template
    with the processed results or an error message.

    Parameters
    ----------
    request : Request
        The HTTP request object.
    input_text : str
        Input text provided by the user, typically a Git repository URL or path.
    slider_position : int
        Position of the slider, representing the maximum file size in the query.
    pattern_type : str
        Type of pattern to use, either "include" or "exclude" (default is "exclude").
    pattern : str
        Pattern to include or exclude in the query, depending on the pattern type.
    is_index : bool
        Flag indicating whether the request is for the index page (default is False).

    Returns
    -------
    _TemplateResponse
        Rendered template response containing the processed results or an error message.
    """
    # Extract owner and repo from input_text
    owner, repo = input_text.split("/")[-2], input_text.split("/")[-1]
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url)

    if response.status_code == 200:
        repo_data = response.json()
    else:
        repo_data = {}

    template = "index.jinja" if is_index else "git.jinja"
    template_response = partial(templates.TemplateResponse, name=template)
    max_file_size = log_slider_to_size(slider_position)

    context = {
        "request": request,
        "repo_url": input_text,
        "examples": EXAMPLE_REPOS if is_index else [],
        "default_file_size": slider_position,
        "pattern_type": pattern_type,
        "pattern": pattern,
        "repo_data": repo_data,
    }

    try:
        # Set a timeout value (in seconds) to prevent long-running operations
        summary, tree, content = await asyncio.wait_for(
            ingest_async(
                source=input_text,
                max_file_size=max_file_size,
                include_patterns=pattern if pattern_type == "include" else None,
                exclude_patterns=pattern if pattern_type == "exclude" else None,
            ),
            timeout=300
        )

    except Exception as e:
        print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
        print(f"{Colors.RED}{e}{Colors.END}")

        context["error_message"] = f"Error: {e}"
        if "405" in str(e):
            context["error_message"] = (
                "Repository not found. Please make sure it is public (private repositories will be supported soon)"
            )
        return template_response(context=context)

    if len(content) > MAX_DISPLAY_SIZE:
        content = (
            f"(Files content cropped to {int(MAX_DISPLAY_SIZE / 1_000)}k characters, "
            "download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        )

    _print_success(
        url=input_text,
        max_file_size=max_file_size,
        pattern_type=pattern_type,
        pattern=pattern,
        summary=summary,
    )

    # Get repository issues data
    repository_issues = get_repository_issues(repo_data, content)

    context.update(
        {
            "result": True,
            "summary": summary,
            "tree": tree,
            "content": content,
            "project_description": get_project_description(tree, content),
            "installation_usage": get_installation_usage(url),
            "general_overview_diagram": get_general_overview_diagram(url, tree),
            "project_metrics": get_project_metrics(repo_data),
            "beginner_issues": repository_issues["beginner_issues"],
            "intermediate_issues": repository_issues["intermediate_issues"],
            "advanced_issues": repository_issues["advanced_issues"],
            "crazy_ideas": repository_issues["crazy_ideas"]
        }
    )

    return template_response(context=context)


def _print_query(url: str, max_file_size: int, pattern_type: str, pattern: str) -> None:
    """
    Print a formatted summary of the query details, including the URL, file size,
    and pattern information, for easier debugging or logging.

    Parameters
    ----------
    url : str
        The URL associated with the query.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    """
    print(f"{Colors.WHITE}{url:<20}{Colors.END}", end="")
    if int(max_file_size / 1024) != 50:
        print(
            f" | {Colors.YELLOW}Size: {int(max_file_size/1024)}kb{Colors.END}", end=""
        )
    if pattern_type == "include" and pattern != "":
        print(f" | {Colors.YELLOW}Include {pattern}{Colors.END}", end="")
    elif pattern_type == "exclude" and pattern != "":
        print(f" | {Colors.YELLOW}Exclude {pattern}{Colors.END}", end="")


def _print_error(
    url: str, e: Exception, max_file_size: int, pattern_type: str, pattern: str
) -> None:
    """
    Print a formatted error message including the URL, file size, pattern details, and the exception encountered,
    for debugging or logging purposes.

    Parameters
    ----------
    url : str
        The URL associated with the query that caused the error.
    e : Exception
        The exception raised during the query or process.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    """
    print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern)
    print(f" | {Colors.RED}{e}{Colors.END}")


def _print_success(
    url: str, max_file_size: int, pattern_type: str, pattern: str, summary: str
) -> None:
    """
    Print a formatted success message, including the URL, file size, pattern details, and a summary with estimated
    tokens, for debugging or logging purposes.

    Parameters
    ----------
    url : str
        The URL associated with the successful query.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    summary : str
        A summary of the query result, including details like estimated tokens.
    """
    estimated_tokens = summary[summary.index("Estimated tokens:") + len("Estimated ") :]
    print(f"{Colors.GREEN}INFO{Colors.END}: {Colors.GREEN}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern)
    print(f" | {Colors.PURPLE}{estimated_tokens}{Colors.END}")
