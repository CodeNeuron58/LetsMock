"""Viva token/API server.

Run it:
    uv run python api.py            # serve on http://localhost:8000

Pairs with the agent worker (run in a second terminal):
    uv run python agent.py dev      # agent joins rooms created via /session
"""

from dotenv import load_dotenv

# Load .env before viva.config / livekit read keys from the environment.
load_dotenv()

import uvicorn  # noqa: E402


def main() -> None:
    uvicorn.run("viva.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
