// src/hooks/useScholarships.js

import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api/client.js";

// When the deck runs down to this many cards left, fetch the next batch so
// the user never hits a dead end mid-session -- the backend already
// excludes anything already swiped, so calling getDeck() again just returns
// the next unswiped batch.
const REFILL_THRESHOLD = 3;

export function useScholarships() {
  const [deck, setDeck] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exhausted, setExhausted] = useState(false);
  const fetchingMore = useRef(false);

  const loadDeck = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { results } = await api.getDeck();
      setDeck(results);
      setExhausted(results.length === 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeck();
  }, [loadDeck]);

  const fetchMore = useCallback(async () => {
    if (fetchingMore.current || exhausted) return;
    fetchingMore.current = true;
    try {
      const { results } = await api.getDeck();
      if (results.length === 0) {
        setExhausted(true);
      } else {
        setDeck((current) => {
          const existingIds = new Set(current.map((item) => item.id));
          const fresh = results.filter((item) => !existingIds.has(item.id));
          return [...current, ...fresh];
        });
      }
    } catch (err) {
      console.error("Failed to load more scholarships:", err.message);
    } finally {
      fetchingMore.current = false;
    }
  }, [exhausted]);

  // Auto-refill once the deck gets low, instead of permanently ending after
  // the first batch.
  useEffect(() => {
    if (!loading && !exhausted && deck.length > 0 && deck.length <= REFILL_THRESHOLD) {
      fetchMore();
    }
  }, [deck.length, loading, exhausted, fetchMore]);

  const swipe = useCallback((scholarshipId, action) => {
    // Optimistically remove the card immediately so the UI feels instant
    setDeck((current) => current.filter((item) => item.id !== scholarshipId));

    // Send the action ("save" or "pass") to the backend
    api.swipeScholarship(scholarshipId, action)
      .then(() => {
        console.log(`Swiped ${action} on scholarship ${scholarshipId}`);
      })
      .catch((err) => {
        console.error("Failed to record swipe:", err.message);
      });
  }, []);

  return { deck, loading, error, reload: loadDeck, swipe };
}
