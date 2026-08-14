"""List stored interviews and their scorecards.

uv run python interviews.py            # one line per interview
uv run python interviews.py <room>     # full scorecard for one interview
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select  # noqa: E402

from viva.scoring.schema import Scorecard  # noqa: E402
from viva.storage.models import Interview, new_session  # noqa: E402


def main() -> None:
    with new_session() as db:
        rows = list(db.scalars(select(Interview).order_by(Interview.created_at.desc())))

    if not rows:
        print("No interviews stored yet. Run an interview first.")
        return

    if len(sys.argv) > 1:
        _show_one(rows, sys.argv[1])
        return

    print(f"{'room':<28} {'mode':<7} {'status':<9} {'score':>6}  created")
    for r in rows:
        score = r.scorecard["assessment"]["overall_score"] if r.scorecard else None
        print(
            f"{r.room:<28} {r.mode:<7} {r.status.value:<9} "
            f"{(f'{score:.1f}' if score is not None else '-'):>6}  "
            f"{r.created_at:%Y-%m-%d %H:%M}"
        )
    print(f"\n{len(rows)} interview(s). Pass a room name to see its full scorecard.")


def _show_one(rows: list[Interview], room: str) -> None:
    match = next((r for r in rows if r.room == room), None)
    if match is None:
        print(f"No interview with room '{room}'.")
        return
    if not match.scorecard:
        print(f"{room}: status={match.status.value}, no scorecard.")
        return

    sc = Scorecard.model_validate(match.scorecard)
    a, m = sc.assessment, sc.metrics
    print(f"=== {room} ({sc.mode}) — {a.overall_score:.1f}/10 ===\n")
    print(f"{a.summary}\n")
    print(
        f"pace {m.words_per_minute:.0f} wpm | {m.filler_word_count} fillers "
        f"{m.filler_breakdown} | {m.candidate_word_count} words\n"
    )
    for label, items in (
        ("Strengths", a.strengths),
        ("Weaknesses", a.weaknesses),
        ("Red flags", a.red_flags),
    ):
        if items:
            print(f"{label}:")
            for i in items:
                print(f"  - {i}")
    print(f"\nStructure: {a.structure_note}\n")
    for i, ans in enumerate(a.per_answer, 1):
        print(f"Q{i} [{ans.score:.1f}/10] {ans.question}")
        print(f"   you said : {ans.what_you_said}")
        print(f"   strong   : {ans.strong_answer}")
        if ans.flags:
            print(f"   flags    : {', '.join(ans.flags)}")
        print()


if __name__ == "__main__":
    main()
