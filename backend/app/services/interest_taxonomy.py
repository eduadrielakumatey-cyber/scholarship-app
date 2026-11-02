"""
app/services/interest_taxonomy.py
------------------------------------
A small, static hierarchy mapping specific/niche interests to the
broader categories they belong to, so a custom interest like "semiconductor
design" or "cybersecurity" (see ProfileSetup's free-text interest field --
frontend/src/components/InterestSelector.jsx) still credits a scholarship
tagged with the broader "engineering" or "computer science", instead of
scoring a flat zero just because the exact strings don't match.

Deliberately NOT a general-purpose synonym engine or embedding-based
similarity search -- that would make match reasons impossible to explain
in plain English (see scoring.py's design principle of only ever showing
deterministic, traceable reasons). This is a hand-maintained, one-directional
map: specific -> broader parent(s). It only ever ADDS credit on top of an
exact match, never replaces it, and never invents a parent for a term
that isn't listed here.

To extend: add an entry mapping a lowercase specific term to a list of
lowercase broader categories it should also be considered a signal for.
Keep this list curated and reviewed -- a bad mapping (e.g. something
overly broad like "art" -> "business") would let irrelevant scholarships
rank higher for the wrong reason.
"""

from __future__ import annotations

# specific/niche interest -> broader categories it should also credit.
# Categories on the right are the sorts of tags actual scholarships list
# (see scholarship.interests) -- broad enough to already exist in the
# database, not new invented tags of their own.
PARENT_CATEGORIES: dict[str, list[str]] = {
    # --- Engineering / hardware / hard sciences ---
    "semiconductor design": ["engineering", "electrical engineering", "stem"],
    "embedded systems": ["engineering", "electrical engineering", "computer science", "stem"],
    "robotics": ["engineering", "mechanical engineering", "computer science", "stem"],
    "electrical engineering": ["engineering", "stem"],
    "mechanical engineering": ["engineering", "stem"],
    "civil engineering": ["engineering", "stem"],
    "chemical engineering": ["engineering", "stem"],
    "aerospace engineering": ["engineering", "stem"],
    "biomedical engineering": ["engineering", "healthcare", "stem"],
    "renewable energy": ["engineering", "environmental science", "stem"],
    "clean energy": ["engineering", "environmental science", "stem"],
    "nuclear engineering": ["engineering", "stem"],
    "materials science": ["engineering", "stem"],

    # --- Computing ---
    "cybersecurity": ["computer science", "stem", "coding"],
    "data science": ["computer science", "stem", "coding"],
    "machine learning": ["computer science", "stem", "coding"],
    "artificial intelligence": ["computer science", "stem", "coding"],
    "software engineering": ["computer science", "coding", "stem"],
    "game development": ["computer science", "coding", "art"],
    "web development": ["computer science", "coding"],
    "coding": ["computer science", "stem"],
    "computer science": ["stem"],

    # --- Arts / design / media ---
    "animation": ["art", "film", "design"],
    "graphic design": ["art", "design"],
    "ux design": ["design", "computer science"],
    "film": ["art", "media"],
    "photography": ["art"],
    "creative writing": ["writing", "art"],
    "journalism": ["writing", "media"],

    # --- Business / entrepreneurship ---
    "entrepreneurship": ["business", "leadership"],
    "finance": ["business"],
    "accounting": ["business"],
    "marketing": ["business"],
    "supply chain management": ["business"],
    "actuarial science": ["business", "stem"],

    # --- Health / life sciences ---
    "biotechnology": ["stem", "healthcare"],
    "public health": ["healthcare"],
    "nursing": ["healthcare"],
    "pre-med": ["healthcare", "stem"],
    "psychology": ["healthcare", "social science"],
    "biology": ["stem", "healthcare"],
    "chemistry": ["stem"],
    "physics": ["stem"],
    "environmental science": ["stem"],

    # --- Trades / vocational ---
    "welding": ["trades"],
    "hvac": ["trades"],
    "automotive technology": ["trades"],
    "culinary arts": ["trades"],
    "electrician": ["trades"],
    "plumbing": ["trades"],

    # --- Civic / other ---
    "public policy": ["leadership", "community service"],
    "law": ["leadership"],
    "aviation": ["engineering", "stem"],
    "agriculture": ["stem"],
}


def expand(tags: set[str]) -> set[str]:
    """
    Given a lowercased set of interest tags, returns the same set plus
    every broader category any of them map to. Purely additive -- never
    removes or renames anything the caller passed in.
    """
    expanded = set(tags)
    for tag in tags:
        expanded.update(PARENT_CATEGORIES.get(tag, []))
    return expanded
