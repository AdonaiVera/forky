import base64
import os
import re
from datetime import datetime, timedelta

import requests
from pyvis.network import Network

from server.ai.gemini_client import GeminiClient

# Initialize the Gemini client
gemini_client = GeminiClient()

def get_github_readme(url: str) -> str:
    """
    Fetch the README file from a GitHub repository.

    Parameters
    ----------
    url : str
        The GitHub API URL for the repository

    Returns
    -------
    str
        The content of the README file, or an empty string if not found
    """
    # Extract owner and repo from the API URL
    parts = url.split('/')
    owner, repo = parts[-2], parts[-1]

    # Construct the URL for the README file
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    try:
        response = requests.get(readme_url)
        if response.status_code == 200:
            # GitHub returns the content as base64 encoded
            content = response.json().get("content", "")
            if content:
                # Decode the base64 content
                decoded_content = base64.b64decode(content).decode('utf-8')
                return decoded_content
        return ""
    except Exception as e:
        print(f"Error fetching README: {e}")
        return ""

def get_project_description(tree: str, content: str) -> dict:
    """
    Generate a project description using the repository structure and content.

    Parameters
    ----------
    tree : str
        String representation of the repository file structure
    content : str
        Content of the repository files

    Returns
    -------
    dict
        Dictionary containing summary, use cases, and contribution insights
    """
    result = gemini_client.analyze_repository(tree, content)
    return result


def get_installation_usage(url: str) -> str:
    """
    Extract installation and usage instructions from a repository's README.

    This function fetches the README content from a GitHub repository URL,
    then uses the Gemini AI model to extract installation and usage instructions.

    Parameters
    ----------
    url : str
        The GitHub repository URL (can be API URL or regular URL)

    Returns
    -------
    str
        Formatted installation and usage instructions extracted from the README,
        including terminal commands for cloning, installing, and running the project
    """
    readme = get_github_readme(url)
    if not readme:
        return "# No README found\n```bash\n# Generic installation\ngit clone [repository-url]\ncd [repository-name]\n```"
    result = gemini_client.get_installation_instructions(readme)
    return result

def get_general_overview_diagram(url, tree) -> str:
    """
    Generate a general overview diagram in HTML format based on the repository structure.
    Note: This feature is currently disabled and will be available in a future update.

    Parameters
    ----------
    tree : str
        String representation of the repository file structure

    Returns
    -------
    str
        HTML code containing a PyVis network visualization of the repository structure
    """

    # Check if the diagram already exists
    diagram_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "diagrams", f"{url.split('/')[-2]}_{url.split('/')[-1]}_diagram.html")
    diagram_name=f"{url.split('/')[-2]}_{url.split('/')[-1]}_diagram.html"
    if os.path.exists(diagram_path):
        return diagram_name

    # Create a new network
    net = Network(height="400px", width="100%", bgcolor="#ffffff", font_color="#000000")

    # Parse the tree structure
    lines = tree.strip().split('\n')
    if len(lines) <= 1:
        return "<div>No structure to display</div>"

    # Skip the "Directory structure:" line if present
    start_idx = 1 if "Directory structure:" in lines[0] else 0

    nodes = {}
    edges = []

    # Process each line in the tree
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not line.strip():
            continue

        # Calculate the depth based on indentation
        depth = (len(line) - len(line.lstrip())) // 4

        # Extract the node name (file or directory)
        node_match = re.search(r'[├└]── (.+?)/?$', line.strip())
        if node_match:
            node_name = node_match.group(1)

            # Add node to the network
            node_id = f"{depth}_{node_name}"

            # Determine node color based on type
            if node_name.endswith('/') or '/' not in line:
                # Directory
                nodes[node_id] = {"name": node_name, "level": depth, "color": "#4ECDC4"}
            else:
                # File
                nodes[node_id] = {"name": node_name, "level": depth, "color": "#FF6B6B"}

            # Connect to parent if not root
            if depth > 0:
                # Find parent (the most recent node with depth-1)
                for j in range(i-1, -1, -1):
                    parent_line = lines[j]
                    parent_depth = (len(parent_line) - len(parent_line.lstrip())) // 4

                    if parent_depth == depth - 1:
                        parent_match = re.search(r'[├└]── (.+?)/?$', parent_line.strip())
                        if parent_match:
                            parent_name = parent_match.group(1)
                            parent_id = f"{parent_depth}_{parent_name}"
                            edges.append((parent_id, node_id))
                            break

    # Add nodes to the network
    for node_id, node_data in nodes.items():
        net.add_node(node_id, label=node_data["name"], color=node_data["color"],
                    title=node_data["name"], size=15)

    # Add edges to the network
    for source, target in edges:
        net.add_edge(source, target)

    # Configure physics
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)

    # Generate HTML
    html = net.generate_html()

    # Save HTML to validate it's correctly created
    try:
        # Extract repo and owner from the URL
        repo_parts = url.split('/')
        owner = repo_parts[-2] if len(repo_parts) >= 2 else "unknown"
        repo = repo_parts[-1] if len(repo_parts) >= 1 else "unknown"

        # Create diagrams directory
        diagrams_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "diagrams")
        os.makedirs(diagrams_dir, exist_ok=True)

        # Save with repo and owner in filename
        with open(diagram_path, "w", encoding="utf-8") as f:
            f.write(html)

        return diagram_name
    except Exception as e:
        print(f"Error saving diagram HTML: {e}")
        return os.path.join(diagrams_dir, f"repo_diagram.html")


def get_project_metrics(repo_data: dict) -> dict:
    """
    Extract key metrics from a GitHub repository's data.

    This function processes repository data from the GitHub API and extracts
    important metrics that provide insights about the repository's popularity,
    activity, and technical details.

    Parameters
    ----------
    repo_data : dict
        Dictionary containing repository data from the GitHub API

    Returns
    -------
    dict
        Dictionary containing key metrics including:
        - stars: Number of stargazers
        - forks: Number of forks
        - open_issues: Count of open issues
        - watchers: Number of watchers
        - contributors: Count of contributors to the repository
        - language: Primary programming language used
        - license: Repository license information
    """
    project_metrics = {
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "watchers": repo_data.get("watchers_count", 0),
        "contributors": len(requests.get(repo_data.get("contributors_url", "")).json()),
        "language": repo_data.get("language", "Unknown"),
        "license": repo_data.get("license", {}).get("name", "No license"),
    }
    return project_metrics


def get_repository_issues(repo_data: dict, content: str) -> dict:
    """
    Fetch and categorize issues from a GitHub repository.

    This function retrieves issues from a GitHub repository and categorizes them
    into beginner, intermediate, and advanced difficulty levels based on labels.
    It also generates some "crazy ideas" for potential contributions.

    Parameters
    ----------
    repo_data : dict
        Dictionary containing repository data from the GitHub API

    Returns
    -------
    dict
        Dictionary containing categorized issues and ideas:
        - beginner_issues: List of issues suitable for beginners
        - intermediate_issues: List of issues of moderate difficulty
        - advanced_issues: List of challenging issues
        - crazy_ideas: List of creative contribution ideas
    """
    try:
        issues_url = repo_data.get("issues_url", "").replace("{/number}", "")
        issues_response = requests.get(f"{issues_url}?state=open")

        if issues_response.status_code != 200:
            return {
                "beginner_issues": [],
                "intermediate_issues": [],
                "advanced_issues": [],
                "crazy_ideas": []
            }

        # Get all issues and filter to only include those from the last 3 months
        all_issues = issues_response.json()

        # Calculate the date 3 months ago from now
        one_year_ago = datetime.now() - timedelta(days=365)

        # Filter issues to only include those created or updated in the last 3 months
        issues = [
            issue for issue in all_issues
            if (datetime.strptime(issue.get("created_at", ""), "%Y-%m-%dT%H:%M:%SZ") > one_year_ago or
                datetime.strptime(issue.get("updated_at", ""), "%Y-%m-%dT%H:%M:%SZ") > one_year_ago)
        ]

        # Get repository name
        repo_name = repo_data.get("name", "")

        # Prepare issues data for the prompt
        issues_data = []
        for issue in issues:
            # Skip pull requests
            if "pull_request" in issue:
                continue

            labels = [label["name"] for label in issue.get("labels", [])]

            # Extract relevant information
            issue_info = {
                "title": issue.get("title", ""),
                "description": issue.get("body", "")[:200] if issue.get("body") else "",
                "labels": labels,
                "link": issue.get("html_url", ""),
                "assigned": issue.get("assignee") is not None
            }
            issues_data.append(issue_info)

        # Use the select_issues method to categorize issues
        categorized_issues = gemini_client.select_issues(issues_data, repo_name, content)

        # Extract issues based on categorization
        beginner_issues = [issues_data[idx] for idx in categorized_issues["beginner_issues"] if idx < len(issues_data)]
        intermediate_issues = [issues_data[idx] for idx in categorized_issues["intermediate_issues"] if idx < len(issues_data)]
        advanced_issues = [issues_data[idx] for idx in categorized_issues["advanced_issues"] if idx < len(issues_data)]

        # Generate a crazy idea
        crazy_idea = gemini_client.generate_crazy_idea(repo_name, content)

        # Limit to a reasonable number for display
        return {
            "beginner_issues": beginner_issues[:5],
            "intermediate_issues": intermediate_issues[:5],
            "advanced_issues": advanced_issues[:5],
            "crazy_ideas": crazy_idea
        }
    except Exception as e:
        print(f"Error retrieving repository issues: {e}")
        return {
            "beginner_issues": [],
            "intermediate_issues": [],
            "advanced_issues": [],
            "crazy_ideas": "Unable to generate ideas at this time."
        }
