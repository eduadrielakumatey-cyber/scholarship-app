"""
scraper/fix_residency.py
------------------------
Fixes listings stored as "national" (states = []) that are really for one
place's residents, which made them show up for students in every state.

  python -m scraper.fix_residency          # dry run: lists what it would change
  python -m scraper.fix_residency --apply  # writes the fixes

Known fixes are listed below by exact title; anything else the residency
check flags is only reported, for a person to look at.
"""

import argparse

from scraper.daily_discovery import residency_mentioned

KNOWN_FIXES = {
    "DC Tuition Assistance Grant (DCTAG)": ["DC"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    from app import create_app
    from app.extensions import db
    from app.models import Scholarship

    app = create_app()
    with app.app_context():
        for title, states in KNOWN_FIXES.items():
            for s in Scholarship.query.filter_by(title=title).all():
                if s.states != states:
                    print(f"{'fixing' if args.apply else 'would fix'}: {s.title}: {s.states} -> {states}")
                    if args.apply:
                        s.states = states
        if args.apply:
            db.session.commit()
        for s in Scholarship.query.filter_by(is_active=True).all():
            phrase = None if s.states else residency_mentioned(s.description)
            if phrase:
                print(f"check by hand: #{s.id} {s.title} (says '{phrase}')")
        print("done" if args.apply else "dry run, nothing written")


if __name__ == "__main__":
    main()
