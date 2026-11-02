// src/components/SwipeDeck.jsx
//
// Renders a small stack (top 3 cards) so the user can see there's more
// behind the current card, but only the front card is interactive. When
// the front card is swiped, it's removed from the deck array and the next
// one becomes the front automatically (driven by the `deck` array order
// from useScholarships).

import { Link } from "react-router-dom";
import SwipeCard from "./SwipeCard.jsx";

export default function SwipeDeck({ deck, onSwipe, onRefresh }) {
  if (deck.length === 0) {
    return (
      <div className="empty-deck">
        <h2>You've seen all your current matches</h2>
        <p>
          New scholarships are added regularly, and widening your profile can unlock more right
          now: previously skipped scholarships get another look whenever they fit a newly
          added interest.
        </p>
        <div className="empty-deck__actions">
          <Link to="/profile" className="primary-button empty-deck__action">
            Update interests
          </Link>
          <Link to="/saved" className="text-link-button empty-deck__action">
            Review saved scholarships
          </Link>
          {onRefresh && (
            <button type="button" className="text-link-button empty-deck__action" onClick={onRefresh}>
              Refresh recommendations
            </button>
          )}
        </div>
      </div>
    );
  }

  const visibleCards = deck.slice(0, 3);

  return (
    <div className="swipe-deck">
      {visibleCards
        .map((scholarship, index) => (
          <SwipeCard
            key={scholarship.id}
            scholarship={scholarship}
            isTop={index === 0}
            onSwiped={(action) => onSwipe(scholarship.id, action)}
          />
        ))
        .reverse() /* reverse so card[0] (the front card) renders LAST,
                       i.e. on top in the DOM stacking order */}
    </div>
  );
}
