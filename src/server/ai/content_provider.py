import base64
import os
import re

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


def get_contribution_guidelines() -> str:
    """
    Provide standard contribution guidelines.

    Returns
    -------
    str
        Text describing how to contribute to the project
    """
    return "To contribute, please fork the repository and submit a pull request with your changes."


def get_community_support() -> str:
    """
    Provide information about community support channels.

    Returns
    -------
    str
        Text describing community support options
    """
    return "Join our community on Discord and follow us on Twitter for updates and support."


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
