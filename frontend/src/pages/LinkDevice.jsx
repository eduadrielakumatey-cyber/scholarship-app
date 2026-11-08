// src/pages/LinkDevice.jsx
//
// /link: open a profile made on another device, using the one-time code
// from that device's Profile page. Scanning the QR lands here with the
// code already in the #fragment.

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

function codeFromHash() {
  return decodeURIComponent(window.location.hash.replace(/^#/, "")).slice(0, 12);
}

export default function LinkDevice() {
  const { user, redeemLinkCode } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState(codeFromHash);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await redeemLinkCode(code);
      // Drop the code from the address bar and history.
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="start-page">
      <div className="screen">
        <h1 className="page-title">Open your profile here</h1>
        <p className="page-subtitle">
          On the device you already use, go to Profile, tap <strong>Get a code</strong>, then
          type it below.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="link-code">Code</label>
            <input
              id="link-code"
              className="device-link__input"
              placeholder="K7QP-4M2X"
              autoComplete="one-time-code"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={12}
              required
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
            />
          </div>

          {user && (
            <p className="field-help">
              This device already has a profile. Opening the other one switches to it, and you
              won't be able to get back to the one here.
            </p>
          )}

          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}

          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? "Opening..." : "Open my profile"}
          </button>
        </form>

        <p className="field-help device-link__alt">
          New to ScholarMatch? <Link to="/start">Start matching instead</Link>
        </p>
      </div>
    </div>
  );
}
