// src/components/guide/GuideTour.jsx
//
// First-run walkthrough: Scout points at one part of the Discover screen
// at a time (spotlight cut-out + speech bubble), with Next / Skip. Shown
// once per browser; "done" is remembered in localStorage (a per-viewer
// convenience -- listed on the Cookie Policy page). Tapping Scout on
// Discover replays it.

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import Guide from "./Guide.jsx";

export const TOUR_DONE_KEY = "scholarmatch_tour_done";

export const DISCOVER_STEPS = [
  {
    target: null,
    mood: "excited",
    message: "Hi, I'm Scout! Let me show you around. It takes 20 seconds.",
  },
  {
    target: ".swipe-card--top .card-body",
    mood: "happy",
    message: "Every card is one scholarship I think you qualify for: the amount, deadline and what it's for.",
  },
  {
    target: ".swipe-card--top .ticket-stub",
    mood: "thinking",
    message: "Down here is why it matched you and how competitive it is. Scroll the card to see it all.",
  },
  {
    target: ".swipe-card--top .round-button--like",
    mood: "wow",
    message: "Like it? Swipe right or tap the heart to save it to your list.",
  },
  {
    target: ".swipe-card--top .round-button--pass",
    mood: "curious",
    message: "Not for you? Swipe left or tap X. I'll learn from it.",
  },
  {
    // Sidebar link on wide screens; on phones the sidebar is tucked away,
    // so point at the menu button instead.
    target: ['.app-nav a[href="/saved"]', ".app-topbar__menu"],
    mood: "happy",
    message: "Everything you save lands in Saved (in the menu), where you can track each application.",
  },
  {
    target: null,
    mood: "excited",
    message: "That's it! Tap me anytime if you want the tour again. Happy swiping!",
  },
];

export function isTourDone() {
  try {
    return window.localStorage.getItem(TOUR_DONE_KEY) === "1";
  } catch {
    return false;
  }
}

function markTourDone() {
  try {
    window.localStorage.setItem(TOUR_DONE_KEY, "1");
  } catch {
    // Storage blocked: the tour will just offer itself again next visit.
  }
}

const PAD = 8;

// A step's target can be one selector or a list of fallbacks; use the
// first one that's actually visible on screen right now.
function findVisible(target) {
  const selectors = Array.isArray(target) ? target : [target];
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && r.right > 0 && r.left < window.innerWidth) return el;
  }
  return null;
}

export default function GuideTour({ steps = DISCOVER_STEPS, onClose }) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState(null);
  const nextRef = useRef(null);
  const step = steps[index];
  const isLast = index === steps.length - 1;

  const finish = useCallback(() => {
    markTourDone();
    onClose();
  }, [onClose]);

  const measure = useCallback(() => {
    const el = step.target ? findVisible(step.target) : null;
    if (!el) {
      setRect(null);
      return;
    }
    el.scrollIntoView({ block: "nearest" });
    const r = el.getBoundingClientRect();
    setRect({ top: r.top - PAD, left: r.left - PAD, width: r.width + PAD * 2, height: r.height + PAD * 2 });
  }, [step.target]);

  useLayoutEffect(() => {
    measure();
  }, [measure]);

  useEffect(() => {
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [measure]);

  useEffect(() => {
    nextRef.current?.focus();
  }, [index]);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") finish();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [finish]);

  // Put the panel on whichever side of the spotlight has more room.
  let panelStyle = { top: "50%", transform: "translate(-50%, -50%)" };
  if (rect) {
    const spaceBelow = window.innerHeight - (rect.top + rect.height);
    panelStyle = spaceBelow > rect.top
      ? { top: rect.top + rect.height + 14 }
      : { bottom: window.innerHeight - rect.top + 14 };
  }

  return (
    <div role="dialog" aria-modal="true" aria-label="ScholarMatch walkthrough">
      <div
        className="tour-spotlight"
        style={rect ?? { top: "50%", left: "50%", width: 0, height: 0 }}
        aria-hidden="true"
      />
      <div className="tour-panel" style={panelStyle}>
        <Guide mood={step.mood} message={step.message} size={88} />
        <div className="tour-panel__controls">
          <div className="tour-panel__dots" aria-hidden="true">
            {steps.map((_, i) => (
              <span key={i} className={`tour-panel__dot ${i === index ? "is-current" : ""}`} />
            ))}
          </div>
          <span className="visually-hidden">
            Step {index + 1} of {steps.length}
          </span>
          <div className="tour-panel__buttons">
            {!isLast && (
              <button type="button" className="text-link-button" onClick={finish}>
                Skip
              </button>
            )}
            <button
              ref={nextRef}
              type="button"
              className="primary-button tour-panel__next"
              onClick={() => (isLast ? finish() : setIndex(index + 1))}
            >
              {isLast ? "Start swiping" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
