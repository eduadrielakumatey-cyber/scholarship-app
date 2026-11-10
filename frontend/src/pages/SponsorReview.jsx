// src/pages/SponsorReview.jsx
//
// /review/:token -- the sponsor's private page: read applications and pick
// winners. The token in the link is the only key, so the page warns them to
// keep it private.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as api from "../api/client.js";

const LABELS = { submitted: "New", winner: "Winner", not_selected: "Not selected" };

export default function SponsorReview() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api.getSponsorReview(token).then(setData).catch((err) => setError(err.message));
  }, [token]);

  async function decide(appId, status) {
    try {
      const updated = await api.decideApplication(token, appId, status);
      setData((d) => ({ ...d, applications: d.applications.map((a) => (a.id === appId ? updated : a)) }));
    } catch (err) {
      setError(err.message);
    }
  }

  if (error && !data) return <div className="start-page"><div className="screen"><p className="error-text">{error}</p></div></div>;
  if (!data) return <div className="start-page"><div className="screen"><p className="page-subtitle">Loading...</p></div></div>;

  const { scholarship: s, applications } = data;
  const winners = applications.filter((a) => a.status === "winner").length;

  return (
    <div className="start-page">
      <div className="screen">
        <h1 className="page-title">{s.title}</h1>
        <p className="page-subtitle">
          {s.approved ? "Live on ScholarMatch" : "Waiting for ScholarMatch to approve it"} ·{" "}
          ${Number(s.award_amount).toLocaleString()} · {s.num_awards} winner{s.num_awards === 1 ? "" : "s"} ·
          due {s.deadline}
        </p>
        <p className="field-help">
          Private page: anyone with this link can see these applications, so don't share it. Use
          applicants' details only to choose and contact winners.
        </p>

        <h2 className="saved-section-title">
          {applications.length} application{applications.length === 1 ? "" : "s"}
          {winners > 0 && ` · ${winners} winner${winners === 1 ? "" : "s"} picked`}
        </h2>
        {applications.length === 0 && (
          <p className="page-subtitle">No applications yet. They'll show up here as students apply.</p>
        )}

        {applications.map((a) => (
          <div key={a.id} className={`review-card review-card--${a.status}`}>
            <div className="review-card__top">
              <strong>{a.full_name}</strong>
              <span className="review-card__status">{LABELS[a.status]}</span>
            </div>
            <p className="review-card__meta">
              {a.school || "School not given"} · <a href={`mailto:${a.email}`}>{a.email}</a> · applied{" "}
              {new Date(a.created_at).toLocaleDateString()}
            </p>
            {a.essay && (
              <>
                <button type="button" className="text-link-button" onClick={() => setOpen(open === a.id ? null : a.id)}>
                  {open === a.id ? "Hide essay" : "Read essay"}
                </button>
                {open === a.id && <p className="review-card__essay">{a.essay}</p>}
              </>
            )}
            <div className="account-settings__actions">
              {a.status !== "winner" && (
                <button type="button" className="secondary-button" onClick={() => decide(a.id, "winner")}>Pick as winner</button>
              )}
              {a.status !== "not_selected" && (
                <button type="button" className="secondary-button" onClick={() => decide(a.id, "not_selected")}>Not selected</button>
              )}
              {a.status !== "submitted" && (
                <button type="button" className="secondary-button" onClick={() => decide(a.id, "submitted")}>Undo</button>
              )}
            </div>
          </div>
        ))}
        {error && <p className="error-text" role="alert">{error}</p>}
      </div>
    </div>
  );
}
