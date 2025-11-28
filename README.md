# Viz Agent

## Overview
Viz Agent is a Google ADK multi-agent workflow. It help's You automate the boring task of data analysis. Why write manual code to know about your dataset when you can upload a file and chat with it. Get response from specialized agent on data quality issues imbalance in data, etc. You can just ask the agent to analyze your data or ask for specific operation's it can handle all.

## Features
- 📁 File-aware chat interface with persistent in-memory session and artifact services.
- 🤖 Multi-agent routing between statistics and visualization specialists.
- 📊 Automatic descriptive statistics, quality checks, and plotting with captured artifacts.

## Setup
1. Create a virtual environment (Python 3.12) and install dependencies:
   ```sh
   uv venv
   source .venv/bin/activate
   uv pip install -r <(python -m pip list --format=freeze)
   ```
   ```sh
   pip install -e .
   ```
2. Provide required environment variables in `.env`. Use `.env.example` for creating env file (API keys for Google ADK/Gemini).
3. Launch Streamlit:
   ```sh
   streamlit run app.py
   ```

## Usage
1. Upload a CSV or text file via the sidebar.
2. Ask analytical or visualization questions; the orchestrator delegates to the appropriate agent.
3. Generated plots appear inline, sourced from artifacts captured by the code executor.

## Project Structure
- [app.py](app.py) — Streamlit UI + ADK service bootstrap.
- [`agents.get_agent_response`](agents.py) — Agent definitions, routing, artifact handling.
- [tools.py](tools.py) — `read_uploaded_file` tool for retrieving stored artifacts.
- [pyproject.toml](pyproject.toml) — Project metadata and dependencies.

## Development Notes
- Agents run with the `Gemini` model and built-in code executor; ensure the runtime supports matplotlib/seaborn/plotly.
- When adding new tools, register them with the appropriate agent and ensure they use the shared artifact service.