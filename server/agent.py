"""LetsMock voice interviewer — LiveKit worker entrypoint.

Run it:
    uv run python agent.py download-files   # one-time: fetch VAD + turn-detector models
    uv run python agent.py console          # talk to it in your terminal (mic + speaker)
    uv run python agent.py dev              # connect a real client via LiveKit Cloud
"""

from dotenv import load_dotenv

# Load .env before the LiveKit worker / plugins read their keys from the environment.
load_dotenv()

from livekit.agents import JobProcess, WorkerOptions, cli  # noqa: E402
from livekit.plugins import silero  # noqa: E402

from viva.agent.entrypoint import entrypoint  # noqa: E402


def prewarm(proc: JobProcess) -> None:
    """Load the VAD model once per worker process rather than once per interview.

    Loading it inside the job cost tens of seconds before the candidate heard
    anything; here it happens while the worker is idle and waiting.
    """
    proc.userdata["vad"] = silero.VAD.load()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
