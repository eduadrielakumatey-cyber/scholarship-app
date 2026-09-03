// src/components/SwipeDeck.jsx
//
// Renders a small stack (top 3 cards) so the user can see there's more
// behind the current card, but only the front card is interactive. When
// the front card is swiped, it's removed from the deck array and the next
// one becomes the front automatically (driven by the `deck` array order
// from useScholarships).

import SwipeCard from "./SwipeCard.jsx";

export default function SwipeDeck({ deck, onSwipe }) {
  if (deck.length === 0) {
    return (
      <div className="empty-deck">
        <h2>You're all caught up</h2>
        <p>
          No more scholarships match your profile right now. New ones get added daily, so check
          back soon -- or update your profile to widen your matches.
        </p>
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
