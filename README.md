# HW5 — University IT Helpdesk with LangGraph

## 1. Project Overview

This project implements a university IT helpdesk assistant using Python, LangGraph, and an LLM.

The assistant supports:
- Wi-Fi troubleshooting
- Password recovery instructions
- Service status checks
- Local support ticket drafts
- Persistent conversation memory
- Separation of student conversation histories

The project uses fictional university helpdesk data.

## 2. Project Structure

- `main.py` — Main LangGraph application
- `tools.py` — Helpdesk tools and ticket authorization
- `memory_demo.py` — SQLite memory demonstration
- `data/` — Helpdesk instructions, service profiles, demo users, and scenarios
- `tests/` — Automated pytest tests
- `outputs/` — Saved scenario logs
- `requirements.txt` — Python dependencies
- `.github/workflows/tests.yml` — GitHub Actions workflow

Generated ticket drafts and local SQLite databases are excluded from Git.

## 3. LangGraph Architecture

The application uses a graph with two main nodes:

1. `chatbot` — The LLM selects an action.
2. `tools` — ToolNode executes the selected tool.

The workflow is:

START -> chatbot -> tools -> chatbot -> END

The assistant can return a final answer without calling a tool.

## 4. Helpdesk Tools

### find_instructions

Retrieves Wi-Fi or password recovery instructions from `helpdesk.json`.

### check_service_status

Checks the selected service profile from `service_status.json`.

Supported profiles:
- normal
- wifi_outage
- recovery_outage
- status_unavailable

Service profiles are selected by application code, not by the LLM.

### prepare_ticket

Creates a local JSON draft, not a submitted university ticket.

The protected tool checks for an explicit ticket request in the latest student message.

The application also prevents conditional ticket creation when the selected service status is not operational.

The current authorization logic is a demonstration and does not implement full production security.

## 5. Conversation Memory

LangGraph uses SQLite checkpointers to save conversation history.

The application provides a helper function that combines user and conversation identifiers into an internal thread ID.

This separates conversation histories in the demo.

Real applications must authenticate users and verify access to their conversations.

## 6. Requirements

- Python 3.13
- Dependencies listed in `requirements.txt`
- OpenAI API key for LLM demonstrations

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure `OPENAI_API_KEY` in your environment before using the LLM.

Never commit an API key to GitHub.

## 7. Running the Application

From the project root:

```bash
python main.py
```

The main script loads the project data and runs a demonstration if an API key is configured.

To demonstrate SQLite memory:

```bash
python memory_demo.py start
python memory_demo.py resume
```

The second command starts a new Python process and reads the saved conversation.

For a fresh memory demonstration, delete only the demo database under `local-storage/`.

## 8. Automated Tests

Run:

```bash
python -m pytest -v tests/
```

The current test suite includes eight tests covering:

- Instruction retrieval
- Service status handling
- Blocking unauthorized ticket creation
- Creating an authorized ticket draft
- Rejecting reuse of old ticket permission
- SQLite memory persistence
- Separation of different threads
- Separation of different student histories

These tests do not require an OpenAI API key.

GitHub Actions is configured to run the test suite on pushes and pull requests.

## 9. Scenario Evidence

The `data/scenarios.json` fixture contains scenarios S01–S14.

Saved evidence files are located in:

`outputs/S01.json` through `outputs/S14.json`

These logs were collected during development.

A complete automated replay runner for all scenarios is not yet included in the main application.

## 10. Security and Limitations

- The system uses fictional demo data.
- API keys must be provided through environment variables.
- Local ticket files are drafts only.
- SQLite databases and generated tickets are excluded from Git.
- Users must not provide passwords or recovery codes.
- The project does not implement production authentication.
- Ticket authorization requires further improvements for complex conversations.
- Full scenario replay and final submission verification remain to be completed.
