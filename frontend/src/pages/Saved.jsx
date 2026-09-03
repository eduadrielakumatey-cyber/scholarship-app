// src/pages/Saved.jsx

import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import * as api from "../api/client.js";
import BottomNav from "../components/BottomNav.jsx";

// The five stages of an application pipeline.
// Order matters — they flow left to right like a progress track.
const STATUSES = [
  { key: "saved",       emoji: "🔖", label: "Saved"       },
  { key: "planning",    emoji: "📝", label: "Planning"     },
  { key: "in_progress", emoji: "🔄", label: "In Progress"  },
  { key: "submitted",   emoji: "✅", label: "Submitted"    },
  { key: "won",         emoji: "🏆", label: "Won!"         },
  { key: "declined",    emoji: "❌", label: "Didn't Win"   },
];

// Color accent for the active status button. Reuses the app's three accent
// tokens instead of a separate color per stage: gold intensifies through
// the in-progress stages (getting closer to submitting), teal marks a win
// (the same "positive value" meaning teal has everywhere else), coral marks
// a decline (same "stop/negative" meaning as the pass button and overdue
// deadlines).
const STATUS_COLORS = {
  saved:       "rgba(242, 181, 68, 0.4)",
  planning:    "rgba(242, 181, 68, 0.65)",
  in_progress: "rgba(242, 181, 68, 0.85)",
  submitted:   "#f2b544",
  won:         "#2ec4b6",
  declined:    "#ff6b6b",
};

function StatusTracker({ scholarshipId, current, onChange }) {
  const [updating, setUpdating] = useState(false);

  async function handleSelect(key) {
    if (key === current || updating) return;
    setUpdating(true);
    try {
      await api.updateScholarshipStatus(scholarshipId, key);
      onChange(scholarshipId, key);
    } catch (err) {
      console.error("Failed to update status:", err.message);
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="status-tracker">
      {STATUSES.map((s) => (
        <button
          key={s.key}
          className={`status-btn ${current === s.key ? "status-btn--active" : ""}`}
          style={current === s.key ? { borderColor: STATUS_COLORS[s.key], color: STATUS_COLORS[s.key] } : {}}
          onClick={() => handleSelect(s.key)}
          disabled={updating}
          title={s.label}
        >
          <span className="status-btn__emoji">{s.emoji}</span>
          <span className="status-btn__label">{s.label}</span>
        </button>
      ))}
    </div>
  );
}

export default function Saved() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const location = useLocation();

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const { results } = await api.getSaved();
      setItems(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [location]);

  function handleStatusChange(scholarshipId, newStatus) {
    setItems((current) =>
      current.map((item) =>
        item.id === scholarshipId ? { ...item, app_status: newStatus } : item
      )
    );
  }

  async function handleRemove(id) {
    setItems((current) => current.filter((item) => item.id !== id));
    try {
      await api.unsaveScholarship(id);
    } catch (err) {
      console.error("Failed to remove:", err.message);
    }
  }

  // Group items by pipeline stage so users see their progress clearly
  const won = items.filter((i) => i.app_status === "won");
  const submitted = items.filter((i) => i.app_status === "submitted");
  const active = items.filter((i) => ["saved", "planning", "in_progress"].includes(i.app_status));
  const declined = items.filter((i) => i.app_status === "declined");

  const totalPotential = items
    .filter((i) => i.app_status !== "declined")
    .reduce((sum, i) => sum + (i.amount || 0), 0);

  const totalWon = won.reduce((sum, i) => sum + (i.amount || 0), 0);

  return (
    <div className="screen">
      <h1 className="page-title">Saved</h1>

      {/* Summary banner */}
      {!loading && items.length > 0 && (
        <div className="saved-summary">
          <div className="saved-summary__stat">
            <span className="saved-summary__value">{items.length}</span>
            <span className="saved-summary__label">scholarships</span>
          </div>
          <div className="saved-summary__divider" />
          <div className="saved-summary__stat">
            <span className="saved-summary__value">${totalPotential.toLocaleString()}</span>
            <span className="saved-summary__label">potential</span>
          </div>
          {totalWon > 0 && (
            <>
              <div className="saved-summary__divider" />
              <div className="saved-summary__stat">
                <span className="saved-summary__value saved-summary__value--won">
                  🏆 ${totalWon.toLocaleString()}
                </span>
                <span className="saved-summary__label">won!</span>
              </div>
            </>
          )}
        </div>
      )}

      {loading && <p className="page-subtitle">Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="empty-state">
          <p>Nothing saved yet. Swipe right on a scholarship in Discover to bookmark it here.</p>
        </div>
      )}

      {/* Active pipeline */}
      {active.length > 0 && (
        <section>
          <h2 className="saved-section-title">In your pipeline</h2>
          {active.map((item) => (
            <SavedCard
              key={item.id}
              item={item}
              onStatusChange={handleStatusChange}
              onRemove={handleRemove}
            />
          ))}
        </section>
      )}

      {/* Submitted */}
      {submitted.length > 0 && (
        <section>
          <h2 className="saved-section-title">Submitted</h2>
          {submitted.map((item) => (
            <SavedCard
              key={item.id}
              item={item}
              onStatusChange={handleStatusChange}
              onRemove={handleRemove}
            />
          ))}
        </section>
      )}

      {/* Won */}
      {won.length > 0 && (
        <section>
          <h2 className="saved-section-title">Won</h2>
          {won.map((item) => (
            <SavedCard
              key={item.id}
              item={item}
              onStatusChange={handleStatusChange}
              onRemove={handleRemove}
            />
          ))}
        </section>
      )}

      {/* Declined */}
      {declined.length > 0 && (
        <section>
          <h2 className="saved-section-title saved-section-title--muted">Didn't win</h2>
          {declined.map((item) => (
            <SavedCard
              key={item.id}
              item={item}
              onStatusChange={handleStatusChange}
              onRemove={handleRemove}
            />
          ))}
        </section>
      )}

      <BottomNav />
    </div>
  );
}

function SavedCard({ item, onStatusChange, onRemove }) {
  const status = item.app_status || "saved";
  const statusMeta = STATUSES.find((s) => s.key === status);

  // Deadline urgency comes straight from the backend's urgency
  // classification (urgent/critical/approaching/normal), the same
  // calculation used in Discover -- not recomputed locally, so the two
  // screens can never disagree about how urgent something is.
  const urgencyClass = item.urgency?.class;
  const daysLeft = item.urgency?.days_left;
  const isUrgent = urgencyClass === "urgent" || urgencyClass === "critical";
  const isOverdue = typeof daysLeft === "number" && daysLeft < 0;

  return (
    <div className="saved-card">
      {/* Top row: amount + status tag */}
      <div className="saved-card__top">
        <span className="saved-card__amount">${item.amount.toLocaleString()}</span>
        <span
          className="saved-card__status-tag"
          style={{ color: STATUS_COLORS[status] || STATUS_COLORS.saved }}
        >
          {statusMeta?.emoji} {statusMeta?.label}
        </span>
      </div>

      <span className={`saved-card__deadline ${isUrgent ? "saved-card__deadline--urgent" : ""} ${isOverdue ? "saved-card__deadline--overdue" : ""}`}>
        {isOverdue
          ? "Deadline passed"
          : isUrgent
          ? `Due in ${daysLeft}d`
          : item.deadline
          ? `Due ${item.deadline}`
          : "Rolling deadline"}
      </span>

      {!item.eligible && (
        <p className="saved-card__ineligible">
          No longer eligible: {(item.ineligible_reasons || []).join("; ") || "profile no longer matches"}
        </p>
      )}

      {/* Title */}
      <h3 className="saved-card__title">
        <Link to={`/scholarship/${item.id}`}>{item.title}</Link>
      </h3>
      <p className="saved-card__org">{item.organization}</p>

      {/* Apply link */}
      {item.source_url && (
        <a
          href={item.source_url}
          target="_blank"
          rel="noreferrer"
          className="card-more-info-link"
        >
          Apply on official site →
        </a>
      )}

      {/* Metrics -- only present when still eligible (see app/services/matching.py) */}
      {item.eligible && item.competitiveness && item.application_value && (
        <div className="saved-card__metrics">
          <span>{item.competitiveness.display}</span>
          <span>${item.application_value.dollars_per_hour_if_won}/hr</span>
          <span>${item.application_value.expected_value} EV</span>
        </div>
      )}

      {/* Application tracker */}
      <StatusTracker
        scholarshipId={item.id}
        current={status}
        onChange={onStatusChange}
      />

      {/* Remove */}
      <button className="saved-card__remove" onClick={() => onRemove(item.id)}>
        Remove
      </button>
    </div>
  );
}
