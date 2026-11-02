// src/components/SwipeCard.jsx

import { useRef, useState } from "react";
import { Heart, X } from "lucide-react";
import ScholarshipMetrics from "./ScholarshipMetrics.jsx";
import { gradeLevelLabel } from "../constants/gradeLevels.js";

const SWIPE_THRESHOLD = 110;

const ALL_COLLEGE_YEARS = ["college_1", "college_2", "college_3", "college_4", "college_5plus"];

// Summarizes a scholarship's grade_levels into one short tag instead of
// concatenating every label (a fully-open scholarship lists all 6 codes,
// which would otherwise read as a wall of text).
function gradeLevelsTag(gradeLevels) {
  const hasSenior = gradeLevels.includes("12");
  const hasAllCollege = ALL_COLLEGE_YEARS.every((c) => gradeLevels.includes(c));
  if (hasSenior && hasAllCollege) return "HS Senior + all college years";
  if (hasAllCollege) return "All college years";
  if (gradeLevels.length === 1) return gradeLevelLabel(gradeLevels[0]);
  return gradeLevels.map(gradeLevelLabel).join(", ");
}

export default function SwipeCard({ scholarship, onSwiped, isTop }) {
  const cardRef = useRef(null);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [flyDirection, setFlyDirection] = useState(null);
  // Set the instant a heart/skip button is clicked (or a drag crosses the
  // threshold) so the button itself can play its confirm animation
  // (heart fill + bounce / skip punch) independently of the card's own
  // fly-off transform -- the two run at the same time, not one blocking
  // the other, so the whole interaction still reads as fast.
  const [confirmedAction, setConfirmedAction] = useState(null);
  const startX = useRef(0);

  function handlePointerDown(e) {
    if (!isTop) return;
    // Without this, pressing a link OR either action button still starts a
    // card drag (pointerdown bubbles up from them to the card), which
    // captures the pointer on the card and swallows the button's own click
    // -- the buttons would visually exist but silently do nothing.
    if (e.target.closest("a, button")) return;
    setDragging(true);
    startX.current = e.clientX;
    cardRef.current?.setPointerCapture?.(e.pointerId);
  }

  function handlePointerMove(e) {
    if (!dragging) return;
    setDragX(e.clientX - startX.current);
  }

  function finishDrag() {
    if (!dragging) return;
    setDragging(false);
    if (dragX > SWIPE_THRESHOLD) {
      triggerFlyOff("right");
    } else if (dragX < -SWIPE_THRESHOLD) {
      triggerFlyOff("left");
    } else {
      setDragX(0);
    }
  }

  function triggerFlyOff(direction) {
    setFlyDirection(direction);
    setConfirmedAction(direction === "right" ? "like" : "pass");
    // Slightly longer than the card's own 220ms fly-off so the button's
    // confirm animation (see .round-button--pop / --punch) has time to
    // read before the card is gone -- still snappy, not a "slow" delay.
    setTimeout(() => onSwiped(direction === "right" ? "save" : "pass"), 260);
  }

  function handleButtonChoice(direction) {
    if (!isTop) return;
    triggerFlyOff(direction);
  }

  const rotation = dragX / 14;
  const translateX = flyDirection === "right" ? 600 : flyDirection === "left" ? -600 : dragX;
  const opacity = flyDirection ? 0 : 1;

  const style = {
    transform: `translateX(${translateX}px) rotate(${flyDirection ? rotation * 3 : rotation}deg)`,
    transition: dragging ? "none" : "transform 220ms ease, opacity 220ms ease",
    opacity,
  };

  const showLikeStamp = dragX > 40 || confirmedAction === "like";
  const showPassStamp = dragX < -40 || confirmedAction === "pass";
  // The heart glyph "fills in" as soon as a save is committed to -- by
  // dragging far enough right or by pressing the button -- instead of
  // always rendering solid, so there's something visible to animate.
  const heartFilled = dragX > 40 || confirmedAction === "like";

  // Build eligibility tags
  const tags = [];
  if (scholarship.min_gpa) tags.push(`GPA ${scholarship.min_gpa}+`);
  if (scholarship.grade_levels && scholarship.grade_levels.length > 0) {
    tags.push(gradeLevelsTag(scholarship.grade_levels));
  }
  if (scholarship.states && scholarship.states.length > 0) {
    tags.push(scholarship.states.join(", "));
  } else {
    tags.push("National");
  }
  if (scholarship.demographics && scholarship.demographics.length > 0) {
    scholarship.demographics.slice(0, 2).forEach((d) => tags.push(d));
  }
  if (scholarship.majors && scholarship.majors.length > 0) {
    tags.push(scholarship.majors[0]);
  }
  if (scholarship.estimated_hours_to_apply) {
    tags.push(`~${scholarship.estimated_hours_to_apply}hr to apply`);
  }
  if (scholarship.num_awards) {
    tags.push(`${scholarship.num_awards} award${scholarship.num_awards > 1 ? "s" : ""}`);
  }

  return (
    <div
      ref={cardRef}
      className={`swipe-card ${isTop ? "swipe-card--top" : "swipe-card--behind"}`}
      style={style}
      // Cards stacked behind the front one are purely decorative: keep
      // their links/buttons out of the tab order and screen readers.
      // (React 18 only passes `inert` through as a string attribute.)
      inert={isTop ? undefined : ""}
      aria-hidden={isTop ? undefined : true}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={finishDrag}
      onPointerCancel={finishDrag}
    >
      {showLikeStamp && <div className="swipe-stamp swipe-stamp--like">INTERESTED</div>}
      {showPassStamp && <div className="swipe-stamp swipe-stamp--pass">SKIP</div>}

      <div className="card-body">
        <div className="card-header">
          <span className="card-amount">${Number(scholarship.amount).toLocaleString()}</span>
          <span className="card-deadline">
            {scholarship.deadline
              ? `Due ${new Date(scholarship.deadline).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}`
              : "Rolling deadline"}
          </span>
        </div>

        <h2 className="card-title">{scholarship.title}</h2>
        <p className="card-org">{scholarship.organization}</p>

        <div className="card-tags">
          {tags.map((tag, i) => (
            <span key={i} className={`card-tag card-tag--${"abcd"[i % 4]}`}>{tag}</span>
          ))}
        </div>

        <p className="card-description">{scholarship.description}</p>
      </div>

      <ScholarshipMetrics scholarship={scholarship} />

      {isTop && (
        <div className="card-actions">
          <button
            type="button"
            className={`round-button round-button--pass ${
              confirmedAction === "pass" ? "round-button--punch" : ""
            }`}
            aria-label="Not interested"
            onClick={() => handleButtonChoice("left")}
          >
            <X size={28} strokeWidth={3} aria-hidden="true" />
          </button>
          <button
            type="button"
            className={`round-button round-button--like ${
              confirmedAction === "like" ? "round-button--pop" : ""
            } ${heartFilled ? "round-button--like-filled" : ""}`}
            aria-label="Interested"
            onClick={() => handleButtonChoice("right")}
          >
            <Heart
              size={26}
              strokeWidth={2.6}
              fill={heartFilled ? "currentColor" : "none"}
              aria-hidden="true"
            />
          </button>
        </div>
      )}
    </div>
  );
}
