# LetsMock

**An AI that interviews you out loud, interrupts you when you ramble, and hands
you a scorecard that doesn't flatter you.**

Reading interview answers doesn't teach you to speak under pressure. LetsMock
runs a real-time voice interview — it asks about your actual resume, follows up
on vague answers, waits when you pause to think — then scores what you said and
how you said it.

Built for the [RevenueCat Shipaton 2026](https://revenuecat-shipaton-2026.devpost.com/).
Site: [letsmock.com](https://letsmock.com)

> The repo and Python package are still named `viva`, the working title.

---

## What it does

**Three rounds**, one interviewer:

| Round | What it does |
| --- | --- |
| **HR / Behavioural** | Motivation, conflict, teamwork. Scored for structure, not vibes |
| **Resume Grill** | Reads your uploaded PDF and asks about your real projects — why that choice, what broke, what you'd redo |
| **CS Fundamentals** | Indexing, concurrency, complexity, API design — spoken aloud, no code editor |

**The scorecard** is the product. It separates two things deliberately:

- **Delivery metrics are computed in code** — filler-word counts, words per
  minute, speaking time. Never asked of the model, so the numbers can't be
  hallucinated. Pace is measured against time *actually spent talking*, so a
  nervous pause doesn't read as slow speech.
- **Judgement comes from the LLM** as schema-validated JSON — a score out of 10,
  per-answer *"what you said → what a strong answer sounds like"*, structure
  notes, and red flags.

---

## Repo layout

Three independent toolchains in one repo:

| Path | What | Toolchain | Run |
| --- | --- | --- | --- |
| `server/` | Voice agent, interview engine, scoring, API | Python / **uv** | `uv run python agent.py console` |
| `app/` | Android client — voice UI, scorecard, paywall | Dart / **Flutter** | `flutter run` |
| `web/` | letsmock.com — landing, privacy, terms | Astro / **pnpm** | `pnpm dev` |

The server holds all the intelligence. The app is a thin WebRTC client: the
phone streams audio and renders results; every decision happens server-side.

---

## How a call works

```
 Flutter app ──POST /session──▶ FastAPI          mints a LiveKit token; the room
      │                                          name carries the mode and the
      │                                          length cap: viva-hr-5-a1b2c3d4
      │
      └──WebRTC audio──▶ LiveKit room ◀── Python agent worker
                                            │
                    Silero VAD + turn detector · Deepgram Nova-3 STT (streaming)
                              → Groq Llama (decides the next question)
                              → Deepgram Aura-2 TTS
                                            │
              interview clock: wrap up near the cap, then end the call
                                            │
        transcript ──▶ metrics (code) + assessment (LLM) ──▶ Scorecard ──▶ SQL
                                            │
 Flutter app ◀──GET /scorecard/{room}────────┘   202 while scoring, 200 when done
```

**Turn-taking is the hard part.** A candidate trails off mid-answer and
continues; a naive silence timer cuts them off. Endpointing is dynamic — short
when the turn detector is confident, up to six seconds when it isn't — so the
interviewer is patient with thinking but still interruptible.

---

## Monetisation

RevenueCat reports *whether* a user has Pro. It does not enforce anything —
[`quota.py`](server/src/viva/quota.py) does:

| | Free | Pro |
| --- | --- | --- |
| Interviews | First one free, then one a week | Unlimited |
| Length | 5 minutes | 15 minutes |

The length cap is enforced by the agent's interview clock, not just advertised.
An exhausted quota returns **402 Payment Required**, which is the app's cue to
open the paywall.

> Voice is not free: roughly ₹10–15 per interview, ~70% of it text-to-speech.
> An unlimited free tier would cost more per user than Pro earns, which is why
> the free tier is weekly rather than daily.

---

## Running it

**Talk to the interviewer with no phone and no LiveKit account:**

```bash
cd server
uv sync
cp .env.example .env      # add your Groq + Deepgram keys
uv run python agent.py console
```

Speak, interrupt it, pause mid-sentence. Hang up with Ctrl-C once and wait ~10s
for the scorecard, then read it:

```bash
uv run python interviews.py           # list interviews
uv run python interviews.py <room>    # the full scorecard
```

**Full stack on a phone** — needs free [LiveKit Cloud](https://cloud.livekit.io) keys in `.env`:

```bash
uv run python api.py              # terminal 1: token + scorecard API
uv run python agent.py dev        # terminal 2: agent worker

adb reverse tcp:8000 tcp:8000     # terminal 3: phone reaches the laptop
cd app && flutter run --dart-define=BACKEND_URL=http://localhost:8000
```

## Tests

```bash
cd server && uv run pytest        # 48 tests
cd app && flutter test
```

The suite covers the free-tier rules, the HTTP surface, resume parsing, the
delivery metrics and the interview clock. The LLM assessment is deliberately
not unit-tested — it costs money per run and isn't deterministic.

---

## Licence

MIT — see [LICENSE](LICENSE). The code is open; the hosted app is a paid
service. You are welcome to self-host your own instance.
