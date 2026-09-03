// src/pages/Login.jsx
//
// Combined login/signup screen (one form, a toggle link switches the
// mode) -- common pattern for small apps where splitting them into two
// routes would just add an extra tap for no benefit.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const loggedInUser = mode === "login"
        ? await login(email, password)
        : await signup(email, password);
      navigate(loggedInUser.profile_complete ? "/" : "/profile");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="screen" style={{ justifyContent: "center" }}>
      <h1 className="page-title">
        Scholar<span className="brand-accent">Match</span>
      </h1>
      <p className="page-subtitle">
        {mode === "login" ? "Welcome back." : "Find scholarships worth your time."}
      </p>
      <div className="ticket-tear--static" aria-hidden="true" />

      <form onSubmit={handleSubmit} style={{ marginTop: 18 }}>
        <div className="field-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
        </button>
      </form>

      <button
        className="text-link-button"
        onClick={() => setMode(mode === "login" ? "signup" : "login")}
      >
        {mode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
      </button>
    </div>
  );
}
