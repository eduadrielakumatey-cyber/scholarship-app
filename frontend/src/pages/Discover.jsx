// src/pages/Discover.jsx
//
// The main screen: the Tinder-style swipe deck. Redirects to profile
// setup first if the user hasn't filled in the fields the matcher needs
// (the backend would 400 on /deck anyway -- checking here avoids that
// round trip and gives a clearer next step).

import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useScholarships } from "../hooks/useScholarships.js";
import SwipeDeck from "../components/SwipeDeck.jsx";
import Guide from "../components/guide/Guide.jsx";
import GuideTour, { isTourDone } from "../components/guide/GuideTour.jsx";

// Scout's reaction after each swipe -- a little variety so it doesn't
// feel like a canned toast.
const SAVE_LINES = ["Saved! Nice pick.", "Ooh, good one. It's in Saved.", "Added to your list!"];
const PASS_LINES = ["No worries, next!", "Skipped. I'll keep looking.", "Not your vibe? On to the next."];

// "We hid 212 awards you can't win" with a tap-to-expand breakdown, so the
// filter reads as work done for the student instead of a thin list.
function FilteredNote({ filtered }) {
  const n = filtered.hidden_count;
  return (
    <details className="filtered-note">
      <summary>
        We hid <strong>{n}</strong> open {n === 1 ? "scholarship" : "scholarships"} you
        can&apos;t win. See why
      </summary>
      <ul>
        {filtered.reasons.map((r) => (
          <li key={r.label}>
            <span>{r.label}</span>
            <span className="filtered-note__count">{r.count}</span>
          </li>
        ))}
      </ul>
      <p className="filtered-note__foot">
        Some miss more than one requirement. Updating your profile can bring them back.
      </p>
    </details>
  );
}

export default function Discover() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { deck, loading, error, filtered, swipe, reload } = useScholarships();
  const [touring, setTouring] = useState(false);
  const [reaction, setReaction] = useState(null);
  const swipeCount = useRef(0);
  const reactionTimer = useRef(0);

  // First visit with cards on screen: start the walkthrough once.
  useEffect(() => {
    if (!loading && !error && deck.length > 0 && !isTourDone()) setTouring(true);
    // location.state.tour is set by the sidebar's "Take the tour" button.
  }, [loading, error, deck.length, location.state?.tour]);

  useEffect(() => () => clearTimeout(reactionTimer.current), []);

  function handleSwipe(id, action) {
    swipe(id, action);
    const lines = action === "save" ? SAVE_LINES : PASS_LINES;
    setReaction({
      mood: action === "save" ? "excited" : "happy",
      message: lines[swipeCount.current++ % lines.length],
    });
    clearTimeout(reactionTimer.current);
    reactionTimer.current = setTimeout(() => setReaction(null), 2600);
  }

  let guide = reaction;
  if (!guide) {
    if (loading) guide = { mood: "thinking", message: "Finding your best matches..." };
    else if (error) guide = { mood: "sad", message: "I couldn't load your matches. Try refreshing." };
    else if (deck.length === 0) guide = { mood: "happy", message: "You've seen everything for now. Add interests to unlock more!" };
    else guide = { mood: "idle", message: null };
  }

  useEffect(() => {
    if (user && !user.profile_complete) {
      navigate("/profile");
    }
  }, [user, navigate]);

  return (
    <div className="deck-screen">
      <div className="discover-header">
        <h1 className="page-title" style={{ marginBottom: 4 }}>
          Discover
        </h1>
        <Guide
          mood={guide.mood}
          message={guide.message}
          size={58}
          bubble="right"
          className="discover-guide"
          onClick={() => setTouring(true)}
          label="Scout, your guide. Replay the walkthrough"
        />
      </div>

      {!loading && !error && deck.length > 0 && (
        <div className="swipe-hint">
          <span className="swipe-hint__side swipe-hint__side--pass">
            <span className="swipe-hint__arrow">←</span> Swipe left to pass
          </span>
          <span className="swipe-hint__side swipe-hint__side--save">
            Swipe right to save <span className="swipe-hint__arrow">→</span>
          </span>
        </div>
      )}

      {!loading && !error && user?.schools == null && deck.some((s) => s.school) && (
        <div className="school-banner" role="note">
          <div>
            <strong>Pick your college first</strong>
            <p>Most of these scholarships are only for students at one college. Pick yours to hide the ones you can&apos;t get.</p>
          </div>
          <Link className="school-banner__button" to="/profile#college">
            Pick my college
          </Link>
        </div>
      )}
      {!loading && !error && filtered?.hidden_count > 0 && <FilteredNote filtered={filtered} />}

      {loading && (
        <p className="page-subtitle">
          Finding your matches... If this is the first visit in a while, the server can take up to
          a minute to wake up.
        </p>
      )}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && <SwipeDeck deck={deck} onSwipe={handleSwipe} onRefresh={reload} />}
      {touring && <GuideTour onClose={() => setTouring(false)} />}
    </div>
  );
}
