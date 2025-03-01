import requests

from server.ai.gemini_client import GeminiClient


def get_project_description(tree, content):
    gemini_client = GeminiClient()
    result = gemini_client.analyze_repository(tree, content)
    print("ANalye")
    print(result)
    return "This is a sample project description. It provides an overview of the project's purpose and features."


def get_installation_usage():
    return "```bash\npip install example-package\nexample-command --help\n```"


def get_general_overview_diagram():
    return "graph TD; A-->B; A-->C; B-->D; C-->D;"


def get_contribution_guidelines():
    return "To contribute, please fork the repository and submit a pull request with your changes."


def get_community_support():
    return "Join our community on Discord and follow us on Twitter for updates and support."


def get_project_metrics(repo_data):
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
