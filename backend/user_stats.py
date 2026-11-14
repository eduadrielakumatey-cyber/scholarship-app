"""
user_stats.py
---------------
How many people are using ScholarMatch. Read-only: it only counts rows, and
it never prints anyone's profile, email or answers.

Run against the live database (PowerShell, from backend/):
    $env:DATABASE_URL = ((Get-Content .env.render | Select-String '^DATABASE_URL=').Line -replace '^DATABASE_URL=','')
    .\\venv\\Scripts\\python.exe user_stats.py

What the numbers mean:
  started        tapped "Start matching" (a device account was created)
  set up         filled in the profile (grade, state, GPA, major)
  swiped         swiped at least one card
  active (7d)    swiped or saved something in the last 7 days
"""

import os
import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL first (see the docstring).")
        return 1
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    now = datetime.utcnow()
    since = {"d1": now - timedelta(days=1), "d7": now - timedelta(days=7), "d30": now - timedelta(days=30)}

    with create_engine(url).connect() as conn:
        def one(sql: str, **params) -> int:
            return conn.execute(text(sql), params).scalar() or 0

        started = one("SELECT count(*) FROM users")
        set_up = one(
            "SELECT count(*) FROM users WHERE gpa IS NOT NULL AND grade_level IS NOT NULL "
            "AND state IS NOT NULL AND major IS NOT NULL"
        )
        swiped = one("SELECT count(DISTINCT user_id) FROM interactions")
        new = {k: one("SELECT count(*) FROM users WHERE created_at >= :t", t=t) for k, t in since.items()}
        active = {
            k: one("SELECT count(DISTINCT user_id) FROM interactions WHERE created_at >= :t", t=t)
            for k, t in since.items()
        }
        swipes = one("SELECT count(*) FROM interactions")
        saves = one("SELECT count(*) FROM interactions WHERE action = 'save'")
        submitted = one("SELECT count(*) FROM interactions WHERE app_status IN ('submitted', 'won', 'declined')")
        won = one("SELECT count(*) FROM interactions WHERE app_status = 'won'")
        daily = conn.execute(text(
            "SELECT date(created_at) AS day, count(*) FROM users "
            "WHERE created_at >= :t GROUP BY day ORDER BY day"
        ), {"t": now - timedelta(days=14)}).all()

    print(f"ScholarMatch users  ({now:%Y-%m-%d %H:%M} UTC)\n")
    print(f"  started      {started:>6}")
    print(f"  set up       {set_up:>6}")
    print(f"  swiped       {swiped:>6}\n")
    print(f"  {'':12} {'24h':>6} {'7 days':>8} {'30 days':>8}")
    print(f"  {'new':12} {new['d1']:>6} {new['d7']:>8} {new['d30']:>8}")
    print(f"  {'active':12} {active['d1']:>6} {active['d7']:>8} {active['d30']:>8}\n")
    print(f"  swipes {swipes}  ·  saves {saves}  ·  applied {submitted}  ·  won {won}\n")
    print("  new users per day (last 14 days)")
    for day, n in daily:
        print(f"    {day}  {'#' * min(n, 60)} {n}")
    if not daily:
        print("    none yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
