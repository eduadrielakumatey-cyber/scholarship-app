// src/pages/Discover.jsx
//
// The main screen: the Tinder-style swipe deck. Redirects to profile
// setup first if the user hasn't filled in the fields the matcher needs
// (the backend would 400 on /deck anyway -- checking here avoids that
// round trip and gives a clearer next step).

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useScholarships } from "../hooks/useScholarships.js";
import SwipeDeck from "../components/SwipeDeck.jsx";
import BottomNav from "../components/BottomNav.jsx";

export default function Discover() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { deck, loading, error, swipe } = useScholarships();

  useEffect(() => {
    if (user && !user.profile_complete) {
      navigate("/profile");
    }
  }, [user, navigate]);

  return (
    <div className="deck-screen">
      <h1 className="page-title" style={{ marginBottom: 4 }}>
        Discover
      </h1>

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

      {loading && <p className="page-subtitle">Finding your matches...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && <SwipeDeck deck={deck} onSwipe={swipe} />}

      <BottomNav />
    </div>
  );
}
