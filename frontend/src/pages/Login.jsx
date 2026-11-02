// src/pages/Login.jsx
//
// Combined login/signup screen (one form, a toggle link switches the
// mode) -- common pattern for small apps where splitting them into two
// routes would just add an extra tap for no benefit.

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import LegalFooter from "../components/LegalFooter.jsx";

export default function Login() {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Signup consents: unchecked by default and never pre-ticked, so
  // agreement is an actual choice. The backend re-checks both.
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const loggedInUser = mode === "login"
        ? await login(email, password)
        : await signup(email, password, {
            age_confirmed: ageConfirmed,
            accepted_terms: acceptedTerms,
          });
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

        {mode === "signup" && (
          <div className="consent-group">
            <label className="consent-check">
              <input
                type="checkbox"
                required
                checked={ageConfirmed}
                onChange={(e) => setAgeConfirmed(e.target.checked)}
              />
              <span>
                I'm at least 13 years old. If I'm under 18, my parent or guardian has said it's OK.
              </span>
            </label>
            <label className="consent-check">
              <input
                type="checkbox"
                required
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <span>
                I agree to the <Link to="/terms">Terms of Service</Link> and{" "}
                <Link to="/privacy">Privacy Policy</Link>.
              </span>
            </label>
          </div>
        )}

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

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

      <LegalFooter />
    </div>
  );
}
