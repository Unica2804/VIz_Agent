# Viz Agent

## Overview
Viz Agent is a Google ADK multi-agent workflow. It help's You automate the boring task of data analysis. Why write manual code to know about your dataset when you can upload a file and chat with it. Get response from specialized agent on data quality issues imbalance in data, etc. You can just ask the agent to analyze your data or ask for specific operation's it can handle all.

## Features
- 📁 File-aware chat interface with persistent in-memory session and artifact services.
- 🤖 Multi-agent routing between statistics and visualization specialists.
- 📊 Automatic descriptive statistics, quality checks, and plotting with captured artifacts.

## Setup
1. Install uv package manager and install dependencies:
   ```sh
   pip install uv 
   
   uv sync
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

### New Chat & Session History
This app supports multiple chat sessions. Use the "+ New Chat" button in the left sidebar to start a brand new chat session. When you click it:
- The current chat messages are saved to the session history.
- A new session ID is created, and the agent runs under that new session.
- Artifacts and plots generated from previous sessions remain available under the chat history.

You can view a previous session by clicking "View <session_id>" to inspect the messages and images in read-only mode, or click "Load <session_id>" to resume that session and continue the conversation.

Note: The app validates user prompts and will reject empty or whitespace-only messages. If the AI API returns an error (400 or similar), the app displays the error in the UI rather than crashing.

## Project Structure
- [app.py](app.py) — Streamlit UI + ADK service bootstrap.
- [`agents.get_agent_response`](agents.py) — Agent definitions, routing, artifact handling.
- [tools.py](tools.py) — `read_uploaded_file` tool for retrieving stored artifacts.
- [pyproject.toml](pyproject.toml) — Project metadata and dependencies.

## Development Notes
- Agents run with the `Gemini` model and built-in code executor; ensure the runtime supports matplotlib/seaborn/plotly.
- When adding new tools, register them with the appropriate agent and ensure they use the shared artifact service.
