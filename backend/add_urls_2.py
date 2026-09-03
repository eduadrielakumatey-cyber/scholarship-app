"""
add_urls_2.py
-------------
DISABLED. Do not re-enable without removing the ID-based matching below.

This script used to assign source_url by hardcoded database row ID
(`Scholarship.query.get(scholarship_id)`), which is unsafe: a row's ID is
not a stable identifier for "which real-world scholarship this is" --
IDs shift whenever rows are inserted, deleted, or reseeded. That is
exactly what happened here: this script was written against one database
state, then run again later against a database whose IDs no longer
lined up with the same scholarships. It silently overwrote 58 correct,
title-matched source_url values (set by add_urls.py, which matches by
title) with URLs belonging to completely unrelated organizations --
e.g. ID 1 was originally "Coca-Cola Scholars Program" and got the URL
intended for "National Society of Professional Engineers Scholarship."

That corruption was found, audited, and repaired -- see
repair_source_urls.py, which fixes source_url the safe way: matching by
exact (title, organization), never by ID, with a validation check before
every write and a full explanation for every change.

If source URLs ever need bulk updating again, extend
repair_source_urls.py's REPAIRS list. Do not resurrect an ID-keyed
mapping for this purpose.
"""

import sys


def run():
    print(
        "add_urls_2.py is permanently disabled: it identified scholarships "
        "by database row ID, which caused a 58-record data corruption "
        "incident (see repair_source_urls.py). Use repair_source_urls.py "
        "instead, which matches by exact title + organization."
    )
    sys.exit(1)


if __name__ == "__main__":
    run()
