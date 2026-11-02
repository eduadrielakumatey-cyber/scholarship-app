// src/pages/Stats.jsx
//
// "Stats for Idiots" -- a Duolingo/Spotify-Wrapped-style summary, not a
// business analytics dashboard. Every number here comes straight from
// GET /api/stats (see backend/app/services/stats.py); this file's only
// job is picking a plain-English sentence and a small visual for each
// one. No number is computed or invented client-side.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api/client.js";
import BottomNav from "../components/BottomNav.jsx";
import StatTile from "../components/stats/StatTile.jsx";
import SaveRateDonut from "../components/stats/SaveRateDonut.jsx";
import DeadlineList from "../components/stats/DeadlineList.jsx";

function formatMoney(value) {
  return `$${Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function titleCase(str) {
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

function gcd(a, b) {
  return b === 0 ? a : gcd(b, a % b);
}

function saveRateSentence(activity) {
  const { saved, viewed } = activity;
  if (saved === 0) {
    return "You haven't saved anything yet. Keep swiping to find ones you like.";
  }
  if (saved === viewed) {
    return "You've saved every scholarship you've seen so far.";
  }
  // "1 out of every N" only reads sensibly below a 50% save rate -- above
  // that (or for an awkward fraction) it collapses to "1 out of every 1",
  // which isn't a sentence. Using the actual reduced fraction handles any
  // rate correctly; a small sample naturally reduces to a clean fraction
  // (2 saved of 3 viewed -> "2 out of every 3"), and a fraction that
  // doesn't reduce to something readable falls back to a plain percentage.
  const divisor = gcd(saved, viewed);
  const num = saved / divisor;
  const den = viewed / divisor;
  if (den <= 10) {
    return `You save about ${num} out of every ${den} scholarships you see.`;
  }
  const rate = Math.round(activity.save_rate_percent ?? 0);
  return `You save about ${rate}% of the scholarships you see.`;
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="screen">
      <h1 className="page-title">Your stats</h1>
      <Link to="/how-it-works" className="text-link-button" style={{ marginBottom: 8, display: "inline-block" }}>
        Curious how predictions work? →
      </Link>

      {loading && <p className="page-subtitle">Crunching your numbers...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && stats && stats.activity.viewed === 0 && (
        <div className="empty-state">
          <p>
            You haven't swiped on anything yet. Start exploring in Discover and your stats will
            show up here.
          </p>
          <Link to="/" className="primary-button" style={{ display: "inline-block", marginTop: 16, width: "auto", padding: "12px 24px" }}>
            Go to Discover
          </Link>
        </div>
      )}

      {!loading && !error && stats && stats.activity.viewed > 0 && (
        <StatsBody stats={stats} />
      )}

      <BottomNav />
    </div>
  );
}

function StatsBody({ stats }) {
  const { activity, money, applications, insights } = stats;
  const saveRate = activity.save_rate_percent ?? 0;

  return (
    <>
      <p className="page-subtitle">A quick look at how it's going, no jargon, promise.</p>

      <section className="stats-section">
        <h2 className="saved-section-title">Your activity</h2>
        <div className="stats-donut-row">
          <SaveRateDonut percent={saveRate} centerValue={`${Math.round(saveRate)}%`} centerLabel="save rate" />
          <p className="stats-plain-sentence">{saveRateSentence(activity)}</p>
        </div>
        <div className="stat-tile-grid">
          <StatTile value={activity.viewed} label="Viewed" />
          <StatTile value={activity.saved} label="Saved" accent="gold" />
          <StatTile value={activity.skipped} label="Skipped" accent="coral" />
          <StatTile value={activity.currently_matching} label="Matching now" accent="teal" />
        </div>
        {activity.strongly_matching > 0 && (
          <p className="stats-plain-sentence">
            You currently have <strong>{activity.strongly_matching}</strong> scholarships that
            strongly match your profile.
          </p>
        )}
      </section>

      {activity.saved > 0 && (
        <section className="stats-section">
          <h2 className="saved-section-title">Money</h2>
          <div className="stat-tile-grid">
            <StatTile value={formatMoney(money.total_saved_value)} label="Total saved value" accent="gold" />
            <StatTile value={formatMoney(money.average_saved_award)} label="Average saved award" />
            {money.highest_saved && (
              <StatTile value={formatMoney(money.highest_saved.amount)} label="Highest saved award" accent="teal" />
            )}
          </div>
          {money.highest_saved && (
            <p className="stats-plain-sentence">
              Your top saved scholarship is <strong>{money.highest_saved.title}</strong>.
            </p>
          )}
        </section>
      )}

      {activity.saved > 0 && (
        <section className="stats-section">
          <h2 className="saved-section-title">Applications</h2>
          <div className="stat-tile-grid">
            <StatTile value={applications.started} label="Started" />
            <StatTile value={applications.submitted} label="Submitted" accent="teal" />
          </div>
          {applications.potential_from_submitted > 0 && (
            <p className="stats-plain-sentence">
              You could still receive <strong>{formatMoney(applications.potential_from_submitted)}</strong> from
              applications you've already submitted.
            </p>
          )}
          {applications.upcoming_deadlines.length > 0 ? (
            <>
              <p className="stats-plain-sentence" style={{ marginTop: 12 }}>
                Coming up:
              </p>
              <DeadlineList deadlines={applications.upcoming_deadlines} />
            </>
          ) : (
            <p className="stats-plain-sentence">No upcoming deadlines on your saved scholarships right now.</p>
          )}
        </section>
      )}

      {(insights.top_saved_category || insights.typical_saved_range) && (
        <section className="stats-section">
          <h2 className="saved-section-title">In plain English</h2>
          <ul className="stats-insight-list">
            {insights.top_saved_category && (
              <li>
                {titleCase(insights.top_saved_category)} scholarships are your most frequently
                saved category.
              </li>
            )}
            {insights.typical_saved_range && (
              <li>
                Most of your saved scholarships are worth{" "}
                {insights.typical_saved_range.max
                  ? `between ${formatMoney(insights.typical_saved_range.min)} and ${formatMoney(
                      insights.typical_saved_range.max
                    )}`
                  : `${formatMoney(insights.typical_saved_range.min)} or more`}
                .
              </li>
            )}
          </ul>
        </section>
      )}
    </>
  );
}
