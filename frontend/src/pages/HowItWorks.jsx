// src/pages/HowItWorks.jsx
//
// A plain-English explainer for the matching/scoring engine that actually
// runs in backend/app/services/scoring.py and matching.py. Every claim on
// this page is a direct description of real code -- eligibility gates,
// Match Quality's three weighted components, the competitiveness RATIO
// (deliberately not framed as a win probability), the expected-value
// formula, and the small preference boost -- not a simplified or invented
// model. Where the example numbers ("87% Match", the $10,000 demo
// scholarship) are illustrative rather than live data, the page says so.

import { useNavigate, Link } from "react-router-dom";
import {
  BookOpen,
  ClipboardList,
  Cog,
  GraduationCap,
  Handshake,
  Info,
  MapPin,
  Sparkles,
  Target,
  User,
} from "lucide-react";

function HeroVisual() {
  return (
    <div className="hiw-hero-visual">
      <div className="hiw-hero-node">
        <span className="hiw-hero-node__icon" aria-hidden="true"><User size={26} strokeWidth={2.2} /></span>
        <span className="hiw-hero-node__label">Your Profile</span>
      </div>
      <span className="hiw-hero-arrow" aria-hidden="true">→</span>
      <div className="hiw-hero-node">
        <span className="hiw-hero-node__icon" aria-hidden="true"><Cog size={26} strokeWidth={2.2} /></span>
        <span className="hiw-hero-node__label">Matching Engine</span>
      </div>
      <span className="hiw-hero-arrow" aria-hidden="true">→</span>
      <div className="hiw-hero-match-ring" role="img" aria-label="Example: 87% match">
        <div className="hiw-hero-match-ring__hole">
          <span className="hiw-hero-match-ring__value">87%</span>
          <span className="hiw-hero-match-ring__label">Match</span>
        </div>
      </div>
    </div>
  );
}

const FACTORS = [
  {
    icon: Target,
    title: "GPA / Academic Performance",
    badge: "Gate + scored factor",
    badgeClass: "mixed",
    text:
      "If a scholarship sets a minimum GPA, you have to meet it to qualify at all. Above that minimum, how much headroom you have feeds your Academic Fit score (30% of Match Quality).",
  },
  {
    icon: GraduationCap,
    title: "Grade Level",
    badge: "Eligibility gate",
    badgeClass: "gate",
    text:
      "Every scholarship lists which grade levels it's open to, from high school senior through 5th-year/grad. If yours isn't on the list, it's filtered out before scoring ever starts.",
  },
  {
    icon: MapPin,
    title: "State / Location",
    badge: "Eligibility gate",
    badgeClass: "gate",
    text:
      "Scholarships restricted to specific states only show up if your profile's state is one of them. National scholarships have no state restriction, so this check is skipped entirely.",
  },
  {
    icon: BookOpen,
    title: "Intended Major",
    badge: "Usually scored",
    badgeClass: "mixed",
    text:
      "Most scholarships treat major as a scoring signal worth 40% of Match Quality, not a strict rule. A small number are flagged as legally major-restricted; for those only, it becomes a hard requirement.",
  },
  {
    icon: Sparkles,
    title: "Interests",
    badge: "Scored · 30%",
    badgeClass: "scored",
    text:
      "We compare your listed interests against a scholarship's own tags, including closely related fields, so \"robotics\" still counts toward a scholarship tagged \"engineering.\"",
  },
  {
    icon: Handshake,
    title: "Demographic Eligibility",
    badge: "Eligibility gate",
    badgeClass: "gate",
    text:
      "Some scholarships are only open to specific demographic groups. If one requires a group that isn't on your profile, it's excluded outright: a strict yes/no check, never a partial score.",
  },
  {
    icon: ClipboardList,
    title: "Scholarship-Specific Numbers",
    badge: "Powers value & urgency",
    badgeClass: "neutral",
    text:
      "Award amount, number of awards, estimated applicant pool, hours to apply, and deadline don't touch your Match Quality score. Instead, they drive the separate Expected Value and Urgency numbers on each card.",
  },
];

const FLOW_STEPS = [
  {
    title: "Student Profile",
    text: "GPA, grade level, state, major, interests, and demographics: exactly what you entered in Profile.",
  },
  {
    title: "Scholarship Requirements",
    text: "The minimums, restrictions, and tags each scholarship lists for itself.",
  },
  {
    title: "Eligibility Check",
    text: "A strict pass/fail: grade level, state, demographics, GPA minimum, and (if flagged) major all have to line up, or the scholarship is dropped completely. Never scored, never shown.",
  },
  {
    title: "Match Analysis",
    text: "For everything that passes, we score Academic Fit, Major Alignment, and Interest Alignment, then blend in Expected Value and a small boost from what you've saved or passed on before.",
  },
  {
    title: "Prediction",
    text: "The result: a Match Quality score, a plain-English reason behind every component, and an overall recommendation score, all shown right on the card.",
  },
];

const SCORE_TIERS = [
  {
    key: "high",
    label: "High Match",
    range: "70-100",
    real: "“Strong fit” / “Excellent fit” in the app",
    text: "Your academic fit, major, and interests line up closely with what the scholarship is actually looking for.",
  },
  {
    key: "medium",
    label: "Medium Match",
    range: "55-69",
    real: "“Good fit” in the app",
    text: "There's real alignment, but at least one factor (often major or interests) isn't a strong match.",
  },
  {
    key: "low",
    label: "Low Match",
    range: "Below 55",
    real: "“Fair fit” in the app",
    text: "You clear the eligibility bar, but the scholarship's focus doesn't overlap much with your profile.",
  },
];

const EXAMPLE_WHY_MATCH = [
  { name: "Academic fit", score: 90, reason: "Your GPA is 0.8 above the 3.0 minimum" },
  { name: "Major alignment", score: 100, reason: "Matches your major: computer science" },
  { name: "Interest alignment", score: 33, reason: "1 of 3 listed interests match (stem)" },
];

export default function HowItWorks() {
  const navigate = useNavigate();

  return (
    <div className="screen hiw-screen">
      <button type="button" className="text-link-button hiw-back" onClick={() => navigate(-1)}>
        ← Back
      </button>

      {/* 1. HERO */}
      <section className="hiw-hero">
        <h1 className="page-title hiw-hero-title">
          How Our Scholarship <span className="brand-accent">Predictions</span> Work
        </h1>
        <p className="page-subtitle hiw-hero-subtitle">
          ScholarMatch reads your profile and a scholarship's own stated requirements, checks
          whether you actually qualify, then scores how well the two line up, so every card
          comes with a reason, not just a number.
        </p>

        <HeroVisual />
        <p className="hiw-hero-caption">
          Example prediction shown for illustration, not a live scholarship.
        </p>
      </section>

      {/* 2. WHAT THE MODEL LOOKS AT */}
      <section className="hiw-section">
        <h2 className="hiw-section-title">What the model looks at</h2>
        <p className="hiw-section-lede">
          Seven inputs feed every prediction. Some are strict yes/no gates; others are scored and
          weighted. Each card says which.
        </p>
        <div className="hiw-factor-grid">
          {FACTORS.map((f) => (
            <div key={f.title} className="hiw-factor-card">
              <span className="hiw-factor-card__icon" aria-hidden="true"><f.icon size={22} strokeWidth={2.2} /></span>
              <span className={`hiw-factor-badge hiw-factor-badge--${f.badgeClass}`}>{f.badge}</span>
              <h3 className="hiw-factor-card__title">{f.title}</h3>
              <p className="hiw-factor-card__text">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 3. HOW THE PREDICTION WORKS */}
      <section className="hiw-section">
        <h2 className="hiw-section-title">How the prediction works</h2>
        <p className="hiw-section-lede">
          Every scholarship goes through the same five-step pipeline, in this exact order.
        </p>
        <ol className="hiw-timeline">
          {FLOW_STEPS.map((step, i) => (
            <li key={step.title} className="hiw-timeline__step">
              <span className="hiw-timeline__marker">{i + 1}</span>
              <div className="hiw-timeline__content">
                <h3 className="hiw-timeline__title">{step.title}</h3>
                <p className="hiw-timeline__text">{step.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* 4. WHAT THE SCORE MEANS */}
      <section className="hiw-section">
        <h2 className="hiw-section-title">What the score means</h2>
        <div className="hiw-tier-grid">
          {SCORE_TIERS.map((tier) => (
            <div key={tier.key} className={`hiw-tier-card hiw-tier-card--${tier.key}`}>
              <span className="hiw-tier-card__label">{tier.label}</span>
              <span className="hiw-tier-card__range">{tier.range}</span>
              <p className="hiw-tier-card__text">{tier.text}</p>
              <p className="hiw-tier-card__real">Shown in-app as {tier.real}</p>
            </div>
          ))}
        </div>
        <p className="hiw-callout">
          A match score estimates <strong>fit</strong>. It is not a probability of winning, and
          not a guarantee of anything.
        </p>
      </section>

      {/* 5. EXPECTED VALUE */}
      <section className="hiw-section">
        <h2 className="hiw-section-title">Expected value: putting a dollar figure on it</h2>
        <p className="hiw-section-lede">
          Expected Value = Award Amount × Competitiveness Ratio, where the Competitiveness Ratio
          is simply awards given ÷ estimated applicant pool. It's a transparent ratio, not a
          calculated win probability: there's no real outcome data (who actually applied, who
          actually won) to calibrate a true probability against.
        </p>

        <div className="hiw-ev-card">
          <p className="hiw-ev-card__label">Example (demo numbers, not a real scholarship)</p>
          <div className="hiw-ev-card__row">
            <span>Award amount</span>
            <span className="stub-value stub-value--money">$10,000</span>
          </div>
          <div className="hiw-ev-card__row">
            <span>Awards given ÷ estimated applicants</span>
            <span className="stub-value stub-value--chance">5 ÷ 500 = 1%</span>
          </div>
          <div className="hiw-ev-card__row hiw-ev-card__row--result">
            <span>Expected value</span>
            <span className="stub-value stub-value--ev">$10,000 × 1% = $100</span>
          </div>
          <div className="hiw-ev-card__row">
            <span>If it takes 10 hours to apply</span>
            <span className="stub-value stub-value--money">$10/hr expected · $1,000/hr if won</span>
          </div>
        </div>
        <p className="hiw-section-footnote">
          On your cards, Expected Value is also ranked as a percentile against your other eligible
          scholarships, so it reflects your best options right now, not just a raw dollar amount.
        </p>
      </section>

      {/* 6. TRANSPARENCY */}
      <section className="hiw-section">
        <h2 className="hiw-section-title">Why we show our reasoning</h2>
        <p className="hiw-section-lede">
          The goal isn't a mysterious score. Every scholarship card includes the exact breakdown
          behind its Match Quality number, so you can see *why* it was recommended.
        </p>
        <div className="hiw-why-example">
          <p className="why-match__title">Why this match</p>
          <ul className="why-match__list">
            {EXAMPLE_WHY_MATCH.map((c) => (
              <li key={c.name} className="why-match__row">
                <span className="why-match__name">{c.name}</span>
                <span className="why-match__score">{c.score}/100</span>
                <span className="why-match__reason">{c.reason}</span>
              </li>
            ))}
          </ul>
          <p className="hiw-why-example__caption">
            This is the same breakdown component shown on every real card in Discover and Saved,
            not a separate mockup.
          </p>
        </div>
      </section>

      {/* 7. DISCLAIMER */}
      <section className="hiw-section">
        <div className="hiw-disclaimer">
          <span className="hiw-disclaimer__icon" aria-hidden="true"><Info size={20} strokeWidth={2.4} /></span>
          <p>
            Predictions are estimates based on the scholarship information we have and the profile
            data you provide. They are not guarantees. Eligibility can change, scholarship
            details can be updated or go stale, and actual scholarship decisions are made entirely
            by the scholarship organizations themselves, not by ScholarMatch.
          </p>
        </div>
      </section>

      <Link
        to="/"
        className="primary-button"
        style={{ display: "block", textAlign: "center", marginTop: 8 }}
      >
        Back to Discover
      </Link>
    </div>
  );
}
