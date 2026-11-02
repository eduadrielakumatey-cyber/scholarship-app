// src/utils/interests.js
//
// Mirrors backend/app/utils/validators.py:normalize_interests -- kept in
// sync manually (small, rarely-changing rule) so custom interests look
// right in the UI immediately, before the round-trip to the server that
// re-applies the same rule as the source of truth.

const MAX_INTEREST_LENGTH = 50;

export function normalizeInterest(raw) {
  if (typeof raw !== "string") return "";
  const cleaned = raw.trim().split(/\s+/).join(" ").toLowerCase();
  if (!cleaned || cleaned.length > MAX_INTEREST_LENGTH) return "";
  return cleaned;
}

// Splits on commas so a user can add several custom interests at once
// (e.g. "Semiconductor Design, Robotics, Embedded Systems"), normalizes
// each, and drops anything empty/too long/already present.
export function parseCustomInterests(raw, existing) {
  const already = new Set(existing.map(normalizeInterest));
  const result = [];
  for (const piece of raw.split(",")) {
    const cleaned = normalizeInterest(piece);
    if (!cleaned || already.has(cleaned)) continue;
    already.add(cleaned);
    result.push(cleaned);
  }
  return result;
}
