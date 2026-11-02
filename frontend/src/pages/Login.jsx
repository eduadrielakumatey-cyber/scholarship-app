// src/pages/Login.jsx
//
// Combined login/signup screen (one form, a toggle link switches the
// mode) -- common pattern for small apps where splitting them into two
// routes would just add an extra tap for no benefit.

import { useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import LegalFooter from "../components/LegalFooter.jsx";
import Guide from "../components/guide/Guide.jsx";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// What Scout says/does for the current state of the form. Order matters:
// errors and in-flight states win over field-level reactions.
function guideReaction({ mode, focused, email, error, submitting, ageConfirmed, acceptedTerms }) {
  if (submitting) return { mood: "excited", message: "Here we go..." };
  if (error) return { mood: "sad", message: `Hmm, that didn't work: ${error}` };
  if (focused === "password") {
    return {
      mood: "shy",
      message: mode === "signup"
        ? "Eyes closed, promise! Pick at least 8 characters."
        : "Not peeking! Type your password.",
    };
  }
  if (focused === "email") {
    if (!email) return { mood: "curious", message: "What's your email?" };
    if (EMAIL_PATTERN.test(email)) return { mood: "happy", message: "That looks like a real email. Nice!" };
    return { mood: "curious", message: "Keep going..." };
  }
  if (mode === "signup" && ageConfirmed && acceptedTerms) {
    return { mood: "happy", message: "All set! Hit Create account and let's find your matches." };
  }
  if (mode === "signup") {
    return { mood: "idle", message: "Hi, I'm Scout! I'll match you with scholarships you can actually win. Setup takes about 2 minutes." };
  }
  return { mood: "idle", message: "Welcome back! Your matches missed you." };
}

export default function Login() {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // The homepage's "Sign up" buttons link to /login?mode=signup.
  const [mode, setMode] = useState(searchParams.get("mode") === "signup" ? "signup" : "login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Signup consents: unchecked by default and never pre-ticked, so
  // agreement is an actual choice. The backend re-checks both.
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [focused, setFocused] = useState(null);
  const emailRef = useRef(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setFocused(null);
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

  const reaction = guideReaction({ mode, focused, email, error, submitting, ageConfirmed, acceptedTerms });

  // While typing an email, Scout's eyes track the end of the text, like
  // it's reading along.
  let lookAt = null;
  if (focused === "email" && emailRef.current) {
    const rect = emailRef.current.getBoundingClientRect();
    const textEnd = Math.min(14 + email.length * 8.5, rect.width - 14);
    lookAt = { x: rect.left + textEnd, y: rect.top + rect.height / 2 };
  }

  return (
    <div className="screen" style={{ justifyContent: "center" }}>
      <Guide mood={reaction.mood} message={reaction.message} lookAt={lookAt} size={104} className="login-guide" />
      <h1 className="page-title">
        <Link to="/" aria-label="ScholarMatch home">
          Scholar<span className="brand-accent">Match</span>
        </Link>
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
            ref={emailRef}
            value={email}
            onFocus={() => setFocused("email")}
            onBlur={() => setFocused(null)}
            onChange={(e) => {
              setEmail(e.target.value);
              setError(null);
            }}
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
            onFocus={() => setFocused("password")}
            onBlur={() => setFocused(null)}
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
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
