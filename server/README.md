# server

The Python side of [LetsMock](../README.md): the LiveKit voice agent, the
interview engine, scoring, and the HTTP API the app talks to.

> The package is still named `viva`, the project's working title.

## Setup

```bash
uv sync
cp .env.example .env   # then fill in your keys
```

Only `GROQ_API_KEY` and `DEEPGRAM_API_KEY` are real requirements. The
`LIVEKIT_*` values must be *set* even for console mode — the worker builds a
LiveKit API client on startup — so `.env.example` ships dummy ones.

## Run

```bash
uv run python agent.py console   # talk to the interviewer in your terminal
uv run python agent.py dev       # agent worker, for a real client via LiveKit
uv run python api.py             # token + scorecard API on :8000
uv run python interviews.py      # list stored interviews and scorecards
uv run pytest                    # 48 tests
```

## Layout

```
agent.py            LiveKit worker entrypoint; loads the VAD model in prewarm
api.py              runs the FastAPI app
interviews.py       dev tool: read stored interviews and scorecards

src/viva/
  config.py         typed settings from the environment
  api.py            POST /session, POST /resume, GET /scorecard/{room}
  quota.py          the free tier — RevenueCat only reports entitlement
  agent/
    entrypoint.py   one job == one interview; wires recorder, clock and scoring
    session.py      the STT -> LLM -> TTS cascade and turn-taking tuning
    interviewer.py  the Agent whose instructions come from the interview mode
  interview/
    modes.py        the three rounds, their prompts, and the room-name encoding
    flow.py         the interview clock: wrap up near the cap, then end
    resume.py       PDF -> text (pypdf; BSD, unlike AGPL PyMuPDF)
  scoring/
    recorder.py     captures turns and real speaking windows from a live call
    metrics.py      filler words and pace, computed in code
    generate.py     transcript -> LLM -> schema-validated Assessment
    schema.py       the Scorecard shape
  storage/
    models.py       interviews and resumes; SQLite now, Postgres by URL swap
    store.py        the only module that touches the ORM

tests/              pytest; each test gets its own throwaway database
```

## Notes

- **Scoring runs in the job's shutdown callback**, which the worker only allows
  ~10s. Fine for short interviews; a long one can be cut off. Moving it to a
  background queue is tracked in `BUILD_PLAN.md`.
- **`is_pro` is client-asserted** and therefore spoofable. It needs verifying
  against RevenueCat's REST API before launch.
