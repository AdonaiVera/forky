# Forky: Your AI code Companion

🌟 Powered by Google Cloud credits through the #VertexAISprint program and developed in the RevolutionUC Hackathon! ✨

[![Forky main page](./docs/frontpage.gif)](https://forky-364607428894.us-central1.run.app/)

Forky helps open-source contributors navigate repos, understand code, and improve pull requests with real-time AI magic powered by Gemini 2.0. Ask questions, get instant PR insights, and receive smart suggestions—all while using RAG, and AI agents to make contributing faster, easier, and way more fun!

🚀 [Try it out!](https://forky-364607428894.us-central1.run.app/)

## 📦 Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run in Local

```bash
cd src/
python -m uvicorn server.main:app --reload
```

## 🚀 Features

### Current Features

- **Repository Analysis**: Deep dive into any GitHub repository with AI-powered insights
- **Code Understanding**: Get instant explanations of code segments and architecture
- **Pull Request Assistant**:
  - Automated PR reviews and suggestions
  - Code quality checks
  - Best practices recommendations
- **Interactive Q&A**: Ask questions about any part of the codebase
- **Visualization Tools**: Visual representation of code dependencies and repository structure
- **Contribution Difficulty Scoring**: Classify in easy, medium, and hard PR.
- **Real-time Suggestions**: Get contextual suggestions while browsing code
- **Multi-language Support**: Works with various programming languages and frameworks

### 🔮 Future Features

- **Repository Matchmaking**: AI-powered suggestions for repositories that match your skills and interests
- **Learning Path Generation**: Personalized learning recommendations based on repository requirements
- **Team Collaboration Tools**: Enhanced features for team-based contributions

## 🏗️ Code Structure

forky/
├── src/
│   ├── server/
│   │   ├── ai/              # AI/ML models and clients
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── templates/       # Jinja2 HTML templates
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── query_processor.py # Query processing logic
│   │   └── server_utils.py  # Utility functions
│   └── static/
│       ├── css/            # Tailwind CSS styles
│       └── js/             # Frontend JavaScript
├── tests/                  # Test suite
├── docs/                   # Documentation
└── docker/                 # Docker configuration

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com) - Frontend
- [PyViz](https://pyviz.org) - Data visualization
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com) - HTML templating
- [posthog](https://github.com/PostHog/posthog) - Amazing analytics
- [gitingest](https://github.com/cyclotruc/gitingest) - Git repository analysis
- [Gemini 2.0](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini) - AI model

## 🌐 Self-host

1. Build the image:

   ```bash
   docker build -t forky .
   ```

2. Run the container:

   ```bash
   docker run -d --name forky -p 8000:8000 forky

   # For local development
   docker run --env-file .env -d --name forky -p 8000:8000 forky
   ```

The application will be available at `http://localhost:8000`.

If you are hosting it on a domain, you can specify the allowed hostnames via env variable `ALLOWED_HOSTS`.

   ```bash
   # Default: "forky.com, *.forky.com, localhost, 127.0.0.1".
   ALLOWED_HOSTS="example.com, localhost, 127.0.0.1"
   ```

## 🤝 Contributing

We welcome contributions!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
