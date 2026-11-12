// src/lib/money.js
//
// Award amounts as students see them. Some college funds don't publish a
// fixed amount; those say "Amount varies" instead of "$0".

export function awardLabel(s, { short = false } = {}) {
  if (s?.amount_varies) return short ? "Varies" : "Amount varies";
  const n = Number(s?.amount ?? s?.award_amount ?? 0);
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}
