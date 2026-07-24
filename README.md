# Viva

An AI interviewer that calls you, grills you on your actual resume, and hands you a brutal scorecard.

Built for the RevenueCat Shipaton 2026.

## Repo layout

This is a monorepo with two independent toolchains:

| Path | What | Toolchain | Run |
|---|---|---|---|
| `server/` | LiveKit voice agent + LangGraph interviewer + FastAPI + async scorecard | Python / **uv** | `uv run python agent.py console` |
| `app/` | Thin Android client (voice UI, paywall) | Dart / **Flutter** | `flutter run` |

The Python `server/` holds all the intelligence. The Flutter `app/` is a thin WebRTC client — the phone just streams audio; every decision happens server-side.

## Voice pipeline (cascade)

```
Flutter app --WebRTC--> LiveKit room --> Python agent worker:
  Silero VAD + turn-detector -> Groq Whisper (STT)
    -> LangGraph interviewer (Groq Llama, in-call)
    -> Deepgram Aura-2 (free) / ElevenLabs Flash (Pro)
Room closes -> transcript -> stronger model -> Pydantic scorecard (async)
```

## Status

Week 0 — scaffolding. See the plan for milestones.
