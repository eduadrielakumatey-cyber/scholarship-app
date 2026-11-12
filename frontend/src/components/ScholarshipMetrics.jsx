// src/components/ScholarshipMetrics.jsx
//
// Renders the explainability payload from the backend's four-layer scoring
// engine (match_quality, competitiveness, application_value, urgency,
// preference_boost, final_score). Every number and reason string shown
// here comes straight from the API -- nothing is generated client-side,
// per the "deterministic explanations, not AI-generated ones" requirement.

import { Link } from "react-router-dom";

function formatMoney(value) {
  return `$${Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function MatchBar({ score, label }) {
  const pct = Math.round(score || 0); // match_quality.score is already 0-100
  // Reuses the app's own three accent tokens instead of a separate scale --
  // strong match reads as teal (the value/success color elsewhere), a weak
  // one as coral (same meaning as "pass" and "overdue").
  const color =
    pct >= 70 ? "var(--color-teal)" :
    pct >= 55 ? "var(--color-gold)" :
    "var(--color-coral)";

  return (
    <div className="match-bar-wrap">
      <div className="match-bar-row">
        <span className="match-bar-label">{label}</span>
        <span className="match-bar-pct">{pct}/100 match</span>
      </div>
      <div className="match-bar-track">
        <div
          className="match-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

const URGENCY_LABELS = {
  critical: "Critical",
  urgent: "Urgent",
  approaching: "Approaching",
  normal: "Normal",
};

function UrgencyBadge({ urgency }) {
  if (!urgency) return null;
  const tier = URGENCY_LABELS[urgency.class] ? urgency.class : "normal";
  const detail =
    urgency.days_left == null
      ? "Rolling deadline"
      : urgency.days_left < 0
      ? "Deadline passed"
      : `${urgency.days_left}d left`;
  return (
    <span className={`urgency-badge urgency-badge--${tier}`}>
      {URGENCY_LABELS[tier]} · {detail}
    </span>
  );
}

// The "why this ranks here" breakdown -- every line is a component the
// scoring engine actually computed, with the plain-English reason it
// returned. No copy is written here beyond static labels.
function WhyThisMatch({ matchQuality, preferenceBoost }) {
  if (!matchQuality) return null;
  return (
    <div className="why-match">
      <p className="why-match__title">Why this match</p>
      <ul className="why-match__list">
        {matchQuality.components.map((c) => (
          <li key={c.name} className="why-match__row">
            <span className="why-match__name">{c.name}</span>
            <span className="why-match__score">{Math.round(c.score)}/100</span>
            <span className="why-match__reason">{c.reason}</span>
          </li>
        ))}
      </ul>
      {typeof preferenceBoost === "number" && preferenceBoost !== 0 && (
        <p className="why-match__preference">
          {preferenceBoost > 0 ? "+" : ""}
          {preferenceBoost} based on scholarships you've liked or saved before
        </p>
      )}
    </div>
  );
}

export default function ScholarshipMetrics({ scholarship }) {
  const {
    eligible,
    ineligible_reasons: ineligibleReasons,
    match_quality: matchQuality,
    competitiveness,
    application_value: applicationValue,
    urgency,
    preference_boost: preferenceBoost,
    final_score: finalScore,
    amount,
    amount_varies: amountVaries,
  } = scholarship;

  if (eligible === false) {
    return (
      <div className="ticket-stub">
        <div className="ticket-tear" aria-hidden="true" />
        <p className="stub-disclaimer" style={{ marginTop: 0 }}>
          No longer eligible: {(ineligibleReasons || []).join("; ") || "profile no longer matches"}
        </p>
        {urgency && <UrgencyBadge urgency={urgency} />}
      </div>
    );
  }

  if (!matchQuality || !applicationValue || !competitiveness) {
    return null; // scored data not present -- nothing meaningful to render
  }

  return (
    <div className="ticket-stub">
      <div className="ticket-tear" aria-hidden="true" />

      {/* Match bar */}
      <MatchBar score={matchQuality.score} label={matchQuality.label} />

      {/* Three key numbers */}
      <div className="stub-grid">
        <div className="stub-cell">
          <span className="stub-value stub-value--chance">{competitiveness.display}</span>
          <span className="stub-label">competitiveness</span>
        </div>
        {/* No published amount means no honest dollar estimate. */}
        <div className="stub-cell">
          <span className="stub-value stub-value--money">
            {amountVaries ? "?" : `${formatMoney(applicationValue.expected_value_per_hour)}/hr`}
          </span>
          <span className="stub-label">exp. value/hr</span>
        </div>
        <div className="stub-cell">
          <span className="stub-value stub-value--ev">{amountVaries ? "?" : formatMoney(applicationValue.expected_value)}</span>
          <span className="stub-label">exp. value</span>
        </div>
      </div>

      {/* Urgency + award row */}
      <div className="stub-meta-row">
        <UrgencyBadge urgency={urgency} />
        <span className="stub-award">Award: {amountVaries ? "amount varies" : formatMoney(amount)}</span>
        {!amountVaries && (
          <span className="stub-dph">{formatMoney(applicationValue.dollars_per_hour_if_won)}/hr if won</span>
        )}
      </div>

      <WhyThisMatch matchQuality={matchQuality} preferenceBoost={preferenceBoost} />

      {typeof finalScore === "number" && (
        <p className="stub-final-score">Overall recommendation score: {Math.round(finalScore)}/100</p>
      )}

      <p className="stub-disclaimer">
        Competitiveness and expected value are estimates based on award size, applicant pool, and
        how well your profile matches. Not a guarantee, and not a calculated probability of
        winning, since we don't have real outcome data to calibrate one.
      </p>

      <Link to="/how-it-works" className="stub-how-link">
        How we calculate this
      </Link>
    </div>
  );
}
