// src/components/AccountSettings.jsx
//
// Log out, download my data, delete my account -- all self-service and on
// the same screen, so exercising a privacy right never requires emailing
// anyone. Email accounts confirm deletion with their password (backend
// enforces it too); device profiles have no password, so the confirm step
// is the button itself. No guilt-trip copy: leaving should be as easy as
// joining.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import * as api from "../api/client.js";

export default function AccountSettings() {
  const { user, logout } = useAuth();
  const isDevice = Boolean(user?.is_device_account);
  const navigate = useNavigate();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  function handleLogout() {
    logout();
    navigate("/");
  }

  async function handleExport() {
    setError(null);
    setBusy(true);
    try {
      const data = await api.exportMyData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "scholarmatch-my-data.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.deleteAccount(isDevice ? null : password);
      logout();
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <section className="account-settings" aria-labelledby="account-heading">
      <h2 id="account-heading" className="account-settings__title">
        Account &amp; privacy
      </h2>
      {isDevice ? (
        <p className="field-help">
          Your profile is saved on this device, with no email or password. Clearing this
          browser's site data or switching devices starts you fresh.
        </p>
      ) : (
        user && <p className="field-help">Signed in as {user.email}</p>
      )}

      <div className="account-settings__actions">
        {!isDevice && (
          <button type="button" className="secondary-button" onClick={handleLogout}>
            Log out
          </button>
        )}
        <button type="button" className="secondary-button" onClick={handleExport} disabled={busy}>
          Download my data
        </button>
        {!confirmingDelete && (
          <button
            type="button"
            className="secondary-button secondary-button--danger"
            onClick={() => setConfirmingDelete(true)}
          >
            {isDevice ? "Delete my profile" : "Delete my account"}
          </button>
        )}
      </div>

      {confirmingDelete && (
        <form className="account-settings__delete" onSubmit={handleDelete}>
          <p>
            This permanently deletes your {isDevice ? "" : "account, "}profile, saved scholarships
            and history. It can't be undone.
          </p>
          {!isDevice && (
          <div className="field-group">
            <label htmlFor="delete-password">Enter your password to confirm</label>
            <input
              id="delete-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          )}
          <div className="account-settings__actions">
            <button
              type="submit"
              className="secondary-button secondary-button--danger"
              disabled={busy}
            >
              {busy ? "Deleting..." : "Permanently delete"}
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setConfirmingDelete(false);
                setPassword("");
                setError(null);
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
