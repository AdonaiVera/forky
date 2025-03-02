
# Forky: Your AI code Companion

🌟 Powered by Google Cloud credits through the #VertexAISprint program and developed in the RevolutionUC Hackathon! ✨

[![Image](./docs/frontpage.gif "Forky main page")](https://gitforky.com)

Forky helps open-source contributors navigate repos, understand code, and improve pull requests with real-time AI magic powered by Gemini 2.0. Ask questions, get instant PR insights, and receive smart suggestions—all while using RAG, and AI agents to make contributing faster, easier, and way more fun!

You can also replace `hub` with `forky` in any GitHub URL to access the corresponding digest.

## 📦 Installation

```bash
python -m venv .venv
   source .venv/bin/activate
pip install -r requirements.txt
```

## Run in Local

```bash
cd src
python -m uvicorn server.main:app --reload
```

## 🚀 Features

- Pending to write

## 🌐 Self-host

1. Build the image:

   ``` bash
   docker build -t forky .

   ```

2. Run the container:

   ``` bash
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

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com) - Frontend
- [PyViz](https://pyviz.org) - Data visualization
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com) - HTML templating
- [posthog](https://github.com/PostHog/posthog) - Amazing analytics
- [gitingest](https://github.com/cyclotruc/gitingest) - Git repository analysis
- [Gemini 2.0](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini) - AI model
