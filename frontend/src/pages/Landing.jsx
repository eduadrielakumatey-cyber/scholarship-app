// src/pages/Landing.jsx
//
// The signed-out homepage. Modeled on the "try it right here" style of
// test-prep landing pages: instead of describing the app, the hero IS a
// small working deck you can swipe, the three steps are clickable panels,
// and the countdown ticks toward a real deadline.
//
// Everything shown comes from GET /api/public/preview (real, verified,
// open scholarships), so nothing on this page is a made-up example. If
// that request fails the page still renders, just without the live bits.

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CalendarClock, Check, ChevronDown, Heart, RotateCcw, ShieldCheck, X } from "lucide-react";
import { getPublicPreview } from "../api/client.js";
import { GRADE_LEVELS, gradeLevelLabel } from "../constants/gradeLevels.js";
import Guide from "../components/guide/Guide.jsx";
import LegalFooter from "../components/LegalFooter.jsx";

const SWIPE_THRESHOLD = 110; // px of drag before a release counts as a swipe
const STEP_ROTATE_MS = 7000;

const DEMO_INTERESTS = ["stem", "leadership", "community service", "arts", "business", "health"];

function formatMoney(amount, { short = false } = {}) {
  if (short && amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`;
  if (short && amount >= 10_000) return `$${Math.round(amount / 1000)}K`;
  return `$${Math.round(amount).toLocaleString()}`;
}

function parseDeadline(iso) {
  // Deadlines are calendar dates; treat them as end of day local time so
  // "due today" still has hours left on it.
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d, 23, 59, 59);
}

function daysLeft(iso) {
  const ms = parseDeadline(iso) - new Date();
  return Math.max(0, Math.floor(ms / 86_400_000));
}

function deadlineLabel(iso) {
  if (!iso) return "Rolling deadline";
  const days = daysLeft(iso);
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  const date = parseDeadline(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return days <= 30 ? `Due ${date} · ${days} days left` : `Due ${date}`;
}

function whoLabel(card) {
  const grades = card.grade_levels.map(gradeLevelLabel).join(", ") || "All students";
  const where = card.states.length ? card.states.join(", ") : "Nationwide";
  return `${grades} · ${where}`;
}

function usePreview() {
  const [preview, setPreview] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    getPublicPreview().then(setPreview).catch(() => setFailed(true));
  }, []);
  return { preview, failed };
}

/* ------------------------------------------------------------------ */
/* Hero demo deck                                                      */
/* ------------------------------------------------------------------ */

function DemoDeck({ cards }) {
  const [index, setIndex] = useState(0);
  const [saved, setSaved] = useState([]);
  const [drag, setDrag] = useState(0);
  const [leaving, setLeaving] = useState(null); // "left" | "right" | null
  const start = useRef(null);

  const current = cards[index];
  const done = index >= cards.length;
  const savedTotal = saved.reduce((sum, c) => sum + c.amount, 0);

  function decide(action) {
    if (!current || leaving) return;
    setLeaving(action === "save" ? "right" : "left");
    setTimeout(() => {
      if (action === "save") setSaved((s) => [...s, current]);
      setIndex((i) => i + 1);
      setLeaving(null);
      setDrag(0);
    }, 260);
  }

  useEffect(() => {
    function onKey(e) {
      if (e.target.closest("input, textarea, select")) return;
      if (e.key === "ArrowRight") decide("save");
      if (e.key === "ArrowLeft") decide("pass");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  function onPointerDown(e) {
    if (leaving) return;
    start.current = e.clientX;
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e) {
    if (start.current !== null) setDrag(e.clientX - start.current);
  }
  function onPointerUp() {
    if (start.current === null) return;
    start.current = null;
    if (drag > SWIPE_THRESHOLD) decide("save");
    else if (drag < -SWIPE_THRESHOLD) decide("pass");
    else setDrag(0);
  }

  // What Scout says depends on what just happened.
  let mood = "idle";
  let message = "Try it! Drag the card, or tap Save / Pass.";
  if (drag > 40) [mood, message] = ["excited", "Ooh, save it!"];
  else if (drag < -40) [mood, message] = ["curious", "Not for you? Pass."];
  else if (done && saved.length) [mood, message] = ["happy", `${formatMoney(savedTotal)} on your list. Imagine a whole deck ranked for you.`];
  else if (done) [mood, message] = ["thinking", "Picky! Your real deck is ranked for your profile."];
  else if (saved.length) [mood, message] = ["happy", `Saved! That's ${formatMoney(savedTotal)} so far.`];

  const offset = leaving === "right" ? 520 : leaving === "left" ? -520 : drag;
  const style = {
    transform: `translateX(${offset}px) rotate(${offset / 18}deg)`,
    transition: start.current !== null ? "none" : "transform 0.26s ease",
  };

  return (
    <div className="demo-deck">
      <Guide mood={mood} message={message} size={84} className="demo-deck__guide" />

      <div className="demo-deck__stack">
        {done ? (
          <div className="demo-card demo-card--end">
            <h3>Your real deck is ranked for you</h3>
            <p>
              Tell us your grade, state and interests, and every card is sorted by how well you fit
              and how much it's worth your time.
            </p>
            <Link to="/start" className="primary-button demo-card__cta">
              Build my deck <ArrowRight size={18} />
            </Link>
            <button
              type="button"
              className="text-link-button"
              onClick={() => {
                setIndex(0);
                setSaved([]);
              }}
            >
              <RotateCcw size={14} /> Swipe again
            </button>
          </div>
        ) : (
          <>
            {cards[index + 1] && (
              <div className="demo-card demo-card--behind" aria-hidden="true" />
            )}
            <article
              key={current.id}
              className="demo-card"
              style={style}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
              aria-label={`${current.title}, ${formatMoney(current.amount)}`}
            >
              <span
                className="demo-card__stamp demo-card__stamp--save"
                style={{ opacity: Math.max(0, Math.min(1, offset / SWIPE_THRESHOLD)) }}
              >
                Save
              </span>
              <span
                className="demo-card__stamp demo-card__stamp--pass"
                style={{ opacity: Math.max(0, Math.min(1, -offset / SWIPE_THRESHOLD)) }}
              >
                Pass
              </span>
              <p className="demo-card__amount">{formatMoney(current.amount)}</p>
              <h3 className="demo-card__title">{current.title}</h3>
              <p className="demo-card__org">{current.organization}</p>
              <p className="demo-card__deadline">
                <CalendarClock size={15} /> {deadlineLabel(current.deadline)}
              </p>
              <p className="demo-card__who">{whoLabel(current)}</p>
              <div className="demo-card__tags">
                {current.renewable && <span className="demo-tag demo-tag--accent">Renewable</span>}
                {current.num_awards > 1 && <span className="demo-tag">{current.num_awards} awards</span>}
                {current.interests.map((i) => (
                  <span key={i} className="demo-tag">{i === "stem" ? "STEM" : i}</span>
                ))}
              </div>
              <p className="demo-card__counter">
                {index + 1} of {cards.length}
              </p>
            </article>
          </>
        )}
      </div>

      {!done && (
        <div className="demo-deck__actions">
          <button type="button" className="demo-action demo-action--pass" onClick={() => decide("pass")} aria-label="Pass">
            <X size={24} />
          </button>
          <span className="demo-deck__hint">← / → keys work too</span>
          <button type="button" className="demo-action demo-action--save" onClick={() => decide("save")} aria-label="Save">
            <Heart size={24} />
          </button>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* "How it works" step panels                                          */
/* ------------------------------------------------------------------ */

function ProfilePanel({ grade, setGrade, interests, setInterests }) {
  return (
    <div className="step-panel">
      <p className="step-panel__label">I'm a...</p>
      <div className="step-chips">
        {GRADE_LEVELS.slice(0, 5).map((g) => (
          <button
            key={g.value}
            type="button"
            className={`step-chip ${grade === g.value ? "is-on" : ""}`}
            aria-pressed={grade === g.value}
            onClick={() => setGrade(g.value)}
          >
            {g.label}
          </button>
        ))}
      </div>
      <p className="step-panel__label">I'm into...</p>
      <div className="step-chips">
        {DEMO_INTERESTS.map((i) => {
          const on = interests.includes(i);
          return (
            <button
              key={i}
              type="button"
              className={`step-chip ${on ? "is-on" : ""}`}
              aria-pressed={on}
              onClick={() => setInterests(on ? interests.filter((x) => x !== i) : [...interests, i])}
            >
              {on && <Check size={14} />} {i === "stem" ? "STEM" : i}
            </button>
          );
        })}
      </div>
      <p className="step-panel__note">The real profile also asks your state, GPA and major. About 2 minutes.</p>
    </div>
  );
}

function RankPanel({ cards, grade }) {
  const open = cards.filter((c) => c.grade_levels.length === 0 || c.grade_levels.includes(grade));
  return (
    <div className="step-panel">
      <p className="step-panel__headline">
        <strong>{open.length}</strong> of these {cards.length} big awards are open to a{" "}
        {gradeLevelLabel(grade)}
      </p>
      <ul className="rank-list">
        {cards.map((c) => {
          const fits = open.includes(c);
          return (
            <li key={c.id} className={`rank-row ${fits ? "" : "is-out"}`}>
              <span className={`rank-row__mark ${fits ? "is-fit" : ""}`}>{fits ? <Check size={14} /> : <X size={14} />}</span>
              <span className="rank-row__title">{c.title}</span>
              <span className="rank-row__amount">{formatMoney(c.amount, { short: true })}</span>
            </li>
          );
        })}
      </ul>
      <p className="step-panel__note">
        {open.length === 0
          ? "None of these fit, which is exactly the scrolling ScholarMatch saves you. Your real deck only shows what you can win."
          : "Change your grade in step 1 and watch this list change. Your real deck hides what you can't win."}
      </p>
    </div>
  );
}

function useCountdown(iso) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!iso) return null;
  const ms = Math.max(0, parseDeadline(iso) - now);
  return {
    days: Math.floor(ms / 86_400_000),
    hours: Math.floor(ms / 3_600_000) % 24,
    minutes: Math.floor(ms / 60_000) % 60,
    seconds: Math.floor(ms / 1000) % 60,
  };
}

function TrackPanel({ next }) {
  const left = useCountdown(next?.deadline);
  if (!next) {
    return (
      <div className="step-panel">
        <p className="step-panel__headline">Saved scholarships live in one list, sorted by deadline.</p>
      </div>
    );
  }
  const units = [
    ["days", left.days],
    ["hrs", left.hours],
    ["min", left.minutes],
    ["sec", left.seconds],
  ];
  return (
    <div className="step-panel">
      <p className="step-panel__label">Next deadline in the catalog</p>
      <p className="step-panel__headline">{next.title}</p>
      <div className="countdown" role="timer" aria-label={`${left.days} days ${left.hours} hours left`}>
        {units.map(([label, value]) => (
          <div key={label} className="countdown__unit">
            <span className="countdown__value">{String(value).padStart(2, "0")}</span>
            <span className="countdown__label">{label}</span>
          </div>
        ))}
      </div>
      <div className="track-statuses">
        <span className="demo-tag">Saved</span>
        <ArrowRight size={14} />
        <span className="demo-tag">Applying</span>
        <ArrowRight size={14} />
        <span className="demo-tag demo-tag--accent">Submitted</span>
      </div>
      <p className="step-panel__note">Mark each one as you go, and never lose track of a due date.</p>
    </div>
  );
}

const STEPS = [
  { title: "Tell us about you", text: "Grade, state, interests. Two minutes, and only what matching needs." },
  { title: "Swipe a ranked deck", text: "Cards you can't win are filtered out. The rest are ranked by fit and payoff." },
  { title: "Track every deadline", text: "Saved awards land in one list with countdowns and application status." },
];

function HowItWorksSteps({ preview }) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const [grade, setGrade] = useState("12");
  const [interests, setInterests] = useState(["stem"]);

  // Auto-advance like a carousel until the visitor touches anything.
  useEffect(() => {
    if (paused) return undefined;
    const t = setTimeout(() => setActive((a) => (a + 1) % STEPS.length), STEP_ROTATE_MS);
    return () => clearTimeout(t);
  }, [active, paused]);

  const cards = preview?.demo_cards ?? [];
  const next = preview?.due_soon?.find((c) => daysLeft(c.deadline) >= 0) ?? null;

  return (
    <section id="how" className="landing-section" onPointerDown={() => setPaused(true)}>
      <h2 className="landing-h2">How it works</h2>
      <div className="steps">
        <ol className="steps__list">
          {STEPS.map((s, i) => (
            <li key={s.title}>
              <button
                type="button"
                className={`steps__item ${active === i ? "is-active" : ""}`}
                aria-pressed={active === i}
                onClick={() => {
                  setActive(i);
                  setPaused(true);
                }}
              >
                <span className="steps__num">{String(i + 1).padStart(2, "0")}</span>
                <span>
                  <span className="steps__title">{s.title}</span>
                  <span className="steps__text">{s.text}</span>
                </span>
                {active === i && !paused && <span className="steps__progress" key={`p${i}`} />}
              </button>
            </li>
          ))}
        </ol>
        <div className="steps__stage">
          {active === 0 && (
            <ProfilePanel grade={grade} setGrade={setGrade} interests={interests} setInterests={setInterests} />
          )}
          {active === 1 && <RankPanel cards={cards} grade={grade} />}
          {active === 2 && <TrackPanel next={next} />}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

const FAQ = [
  {
    q: "Is ScholarMatch free?",
    a: "Yes, and there's no sign-up. Building your deck and tracking deadlines are free, and your profile stays on your device.",
  },
  {
    q: "Where do the scholarships come from?",
    a: "Each listing links to the provider's own official page, not a middleman's copy. Links are re-checked regularly, and dead or expired listings are taken out of decks.",
  },
  {
    q: "Should I ever pay to apply?",
    a: "No. Real scholarships don't charge application fees. New listings that ask for one are rejected before they reach your deck.",
  },
  {
    q: "Can I use it on my phone and my laptop?",
    a: "Yes. On the device you started on, open Profile and tap Get a code. Then scan the QR code or type the code at /link on the other device. Your profile and saved scholarships come with you.",
  },
  {
    q: "What happens to my information?",
    a: "Your profile is only used to rank your matches. You can download your data or delete your account at any time from Settings.",
  },
];

export default function Landing() {
  const { preview, failed } = usePreview();
  const cards = preview?.demo_cards ?? [];

  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="landing-nav__brand">
          Scholar<span className="brand-accent">Match</span>
        </Link>
        <nav className="landing-nav__links" aria-label="Homepage sections">
          <a href="#how">How it works</a>
          <a href="#due">Due soon</a>
          <a href="#faq">FAQ</a>
        </nav>
        <div className="landing-nav__auth">
          <Link to="/start" className="landing-btn landing-btn--dark">Start matching</Link>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero__copy">
          <h1 className="landing-h1">
            Scholarships you can <span className="landing-underline">actually win</span>
          </h1>
          <p className="landing-lede">
            Stop scrolling through lists you don't qualify for. ScholarMatch filters out the
            awards you can't get, ranks the rest by fit and payoff, and keeps every deadline in
            one place.
          </p>
          <div className="landing-ctas">
            <Link to="/start" className="landing-btn landing-btn--dark landing-btn--lg">
              Start matching, no sign-up <ArrowRight size={18} />
            </Link>
            <a href="#how" className="landing-btn landing-btn--ghost landing-btn--lg">See how it works</a>
          </div>
          <p className="landing-link-device">
            Already using ScholarMatch on another device? <Link to="/link">Enter your code</Link>
          </p>
          {preview && (
            <p className="landing-note">
              <ShieldCheck size={16} aria-hidden="true" />
              {preview.live_count} scholarships open right now, worth{" "}
              {formatMoney(preview.total_value, { short: true })} combined. Every link goes to the
              provider's own site.
            </p>
          )}
        </div>
        <div className="landing-hero__demo">
          {cards.length > 0 ? (
            <DemoDeck cards={cards} />
          ) : (
            <div className="demo-deck">
              <Guide
                mood={failed ? "sad" : "thinking"}
                message={failed ? "Couldn't load the demo right now. Tap Start to see your matches!" : "Shuffling the deck..."}
                size={84}
                className="demo-deck__guide"
              />
              <div className="demo-deck__stack">
                <div className="demo-card demo-card--skeleton" aria-hidden="true" />
              </div>
            </div>
          )}
        </div>
      </section>

      <HowItWorksSteps preview={preview} />

      {preview?.due_soon?.length > 0 && (
        <section id="due" className="landing-section">
          <h2 className="landing-h2">Deadlines coming up</h2>
          <ul className="due-list">
            {preview.due_soon.map((c) => {
              const days = daysLeft(c.deadline);
              return (
                <li key={c.id} className="due-row">
                  <span className={`due-row__days ${days <= 3 ? "is-urgent" : ""}`}>
                    {days === 0 ? <strong>Today</strong> : <><strong>{days}</strong> {days === 1 ? "day" : "days"}</>}
                  </span>
                  <span className="due-row__main">
                    <span className="due-row__title">{c.title}</span>
                    <span className="due-row__who">{whoLabel(c)}</span>
                  </span>
                  <span className="due-row__amount">{formatMoney(c.amount)}</span>
                </li>
              );
            })}
          </ul>
          <Link to="/start" className="landing-btn landing-btn--ghost">
            See which ones you qualify for <ArrowRight size={16} />
          </Link>
        </section>
      )}

      <section id="faq" className="landing-section">
        <h2 className="landing-h2">Questions</h2>
        <div className="faq">
          {FAQ.map((f) => (
            <details key={f.q} className="faq__item">
              <summary>
                {f.q} <ChevronDown size={18} className="faq__chevron" />
              </summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="landing-final">
        <Guide mood="happy" message="I'll be right here to walk you through it." size={96} bubble="below" />
        <h2 className="landing-h2">Your deck is two minutes away</h2>
        <Link to="/start" className="landing-btn landing-btn--dark landing-btn--lg">
          Start matching, no sign-up <ArrowRight size={18} />
        </Link>
      </section>

      <div className="landing-footer">
        <LegalFooter />
      </div>
    </div>
  );
}
