// src/pages/Admin.jsx
//
// /admin -- approve or reject scholarships sponsors posted. Unlocked with
// the ADMIN_KEY set on the server; the key is kept only for this browser
// tab (sessionStorage) and is never put in a URL.

import { useState } from "react";
import * as api from "../api/client.js";

const KEY = "scholarmatch_admin_key";

function readKey() {
  try {
    return window.sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export default function Admin() {
  const [key, setKey] = useState(readKey);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  async function load(k = key) {
    setError(null);
    try {
      const { results } = await api.adminPending(k);
      setRows(results);
      try {
        window.sessionStorage.setItem(KEY, k);
      } catch {
        // storage blocked: works until the page closes
      }
    } catch (err) {
      setError(err.message === "not allowed" ? "Wrong key, or ADMIN_KEY isn't set on the server." : err.message);
    }
  }

  async function act(fn, id) {
    try {
      await fn(key, id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="start-page">
      <div className="screen">
        <h1 className="page-title">Sponsor scholarships</h1>
        {rows === null ? (
          <form onSubmit={(e) => { e.preventDefault(); load(); }}>
            <div className="field-group">
              <label htmlFor="admin-key">Admin key</label>
              <input id="admin-key" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)} />
            </div>
            <button className="primary-button" type="submit">Unlock</button>
          </form>
        ) : (
          <>
            {rows.length === 0 && <p className="page-subtitle">Nothing posted yet.</p>}
            {rows.map((s) => (
              <div key={s.id} className="review-card">
                <div className="review-card__top">
                  <strong>{s.title}</strong>
                  <span className="review-card__status">{s.approved ? "Live" : "Waiting"}</span>
                </div>
                <p className="review-card__meta">
                  {s.organization} · ${Number(s.award_amount).toLocaleString()} × {s.num_awards} · due {s.deadline} ·{" "}
                  {s.states?.join(", ") || "national"} · {s.sponsor_name} ({s.sponsor_email})
                </p>
                <p className="review-card__essay">{s.description}</p>
                {s.essay_prompt && <p className="field-help">Essay: {s.essay_prompt}</p>}
                <div className="account-settings__actions">
                  {!s.approved && (
                    <button type="button" className="secondary-button" onClick={() => act(api.adminApprove, s.id)}>Approve</button>
                  )}
                  <button type="button" className="secondary-button secondary-button--danger"
                    onClick={() => window.confirm(`Delete "${s.title}" and any applications to it?`) && act(api.adminReject, s.id)}>
                    {s.approved ? "Take down" : "Reject"}
                  </button>
                </div>
              </div>
            ))}
          </>
        )}
        {error && <p className="error-text" role="alert">{error}</p>}
      </div>
    </div>
  );
}
