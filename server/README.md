# viva-server

Python backend for Viva: the LiveKit voice interviewer agent, the interview engine, and async scorecard scoring.

## Setup

```bash
uv sync
cp .env.example .env   # then fill in your keys
```

## Run the interviewer in the terminal (no phone needed)

```bash
uv run python agent.py console
```

## Layout

```
agent.py              # LiveKit worker entrypoint (thin)
src/viva/
  config.py           # typed settings from env
  agent/              # the voice agent (session, persona, prompts)
  interview/          # interview modes (HR / Resume Grill / SDE)
  scoring/            # Pydantic scorecard schema (async post-call)
```
