// src/pages/Apply.jsx
//
// /apply/:id -- applying from inside ScholarMatch.
//
// Scholarships posted on ScholarMatch by a sponsor (hosted) are applied to
// right here: name, email, essay, submit. Everything else is submitted on
// the provider's own form (no app can submit those for you), so this page
// walks through it: check you qualify, write the essay here (saved to your
// essay library), copy it, open the official form, then mark it submitted.

import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CheckCircle2, ExternalLink, Trophy } from "lucide-react";
import * as api from "../api/client.js";
import EssayEditor, { wordCount } from "../components/EssayEditor.jsx";
import QuestionList from "../components/QuestionList.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const GRADE_LABELS = {
  12: "High school seniors",
  college_1: "College freshmen",
  college_2: "College sophomores",
  college_3: "College juniors",
  college_4: "College seniors",
  college_5plus: "5th-year and graduate students",
};

function money(n) {
  return `$${Number(n || 0).toLocaleString()}`;
}

function Requirements({ s }) {
  const items = [];
  if (s.grade_levels?.length) items.push(`Open to: ${s.grade_levels.map((g) => GRADE_LABELS[g] || g).join(", ")}`);
  items.push(s.states?.length ? `Where: ${s.states.join(", ")} students` : "Where: anywhere in the U.S.");
  if (s.min_gpa) items.push(`GPA: ${s.min_gpa} or higher`);
  items.push(s.essay_required ? "Essay: required" : "Essay: none");
  return (
    <ul className="apply-reqs">
      {items.map((t) => (
        <li key={t}>{t}</li>
      ))}
    </ul>
  );
}

function Header({ s }) {
  return (
    <>
      <Link to="/saved" className="text-link-button">
        ← Back to saved
      </Link>
      <h1 className="page-title" style={{ marginTop: 12 }}>
        {s.title}
      </h1>
      <p className="page-subtitle">
        {s.organization} · {s.amount_varies ? "Amount varies" : money(s.award_amount)} ·{" "}
        {s.deadline ? `Due ${new Date(`${s.deadline}T00:00`).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}` : "Rolling deadline"}
      </p>
    </>
  );
}

function IneligibleNote({ s }) {
  if (s.eligible !== false) return null;
  return (
    <p className="apply-warning" role="note">
      Your profile doesn't match this one: {(s.ineligible_reasons || []).join("; ") || "check the requirements"}.
    </p>
  );
}

// --- Posted on ScholarMatch: apply right here -------------------------------------

function HostedApply({ s }) {
  const { user } = useAuth();
  const [application, setApplication] = useState(undefined); // undefined = loading
  const [form, setForm] = useState({ full_name: user?.full_name || "", email: user?.email || "", school: "" });
  const [essay, setEssay] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const onText = useCallback((t) => setEssay(t), []);

  useEffect(() => {
    api.getMyApplication(s.id).then(setApplication).catch(() => setApplication(null));
  }, [s.id]);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const created = await api.applyInApp(s.id, { ...form, essay, share_consent: consent });
      setApplication(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function withdraw() {
    setBusy(true);
    try {
      await api.withdrawApplication(s.id);
      setApplication(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (application === undefined) return <p className="page-subtitle">Loading...</p>;

  if (application) {
    const won = application.status === "winner";
    return (
      <div className={`apply-done ${won ? "apply-done--won" : ""}`}>
        {won ? <Trophy size={28} aria-hidden="true" /> : <CheckCircle2 size={28} aria-hidden="true" />}
        <h2>
          {won ? "You won!" : application.status === "not_selected" ? "Not selected this time" : "Application submitted"}
        </h2>
        <p>
          {won
            ? `${s.organization} picked you. They'll contact you at ${application.email} about the award.`
            : application.status === "not_selected"
            ? "The sponsor chose another applicant. Keep going: there are more on your deck."
            : `Sent to ${s.organization}. If you win, they'll email ${application.email}. You'll also see it here.`}
        </p>
        {application.status === "submitted" && (
          <button type="button" className="secondary-button" onClick={withdraw} disabled={busy}>
            Withdraw application
          </button>
        )}
        {error && <p className="error-text" role="alert">{error}</p>}
      </div>
    );
  }

  return (
    <form className="apply-form" onSubmit={submit}>
      <p className="apply-badge">Apply right here: this scholarship was posted on ScholarMatch.</p>
      <IneligibleNote s={s} />

      <div className="field-group">
        <label htmlFor="full_name">Your full name</label>
        <input id="full_name" required autoComplete="name" value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
      </div>
      <div className="field-group">
        <label htmlFor="app_email">Email (only the sponsor sees it, to contact a winner)</label>
        <input id="app_email" type="email" required autoComplete="email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
      </div>
      <div className="field-group">
        <label htmlFor="school">School (optional)</label>
        <input id="school" value={form.school} onChange={(e) => setForm({ ...form, school: e.target.value })} />
      </div>

      {s.essay_prompt && <EssayEditor prompt={s.essay_prompt} onTextChange={onText} />}

      <label className="consent-check">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
        <span>
          Share my name, email, school{s.essay_prompt ? " and essay" : ""} with {s.organization} so they can
          review my application and contact me if I win.
        </span>
      </label>

      {error && <p className="error-text" role="alert">{error}</p>}

      <button className="primary-button" type="submit"
        disabled={busy || s.eligible === false || (s.essay_prompt && wordCount(essay) < 25)}>
        {busy ? "Sending..." : "Submit application"}
      </button>
      {s.essay_prompt && wordCount(essay) < 25 && (
        <p className="field-help">Write at least 25 words to submit.</p>
      )}
    </form>
  );
}

// --- Everywhere else: guided apply on the official form -----------------------------

function OutsideApply({ s }) {
  const [submitted, setSubmitted] = useState(s.app_status === "submitted");
  const [error, setError] = useState(null);
  const needsEssay = s.essay_required === true;

  async function markDone() {
    setError(null);
    try {
      await api.markSubmitted(s.id);
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <ol className="apply-steps">
      <li>
        <h2>Check you qualify</h2>
        <IneligibleNote s={s} />
        <Requirements s={s} />
        {s.description && <p className="apply-desc">{s.description}</p>}
      </li>

      <li>
        <h2>Answer their questions</h2>
        {(s.questions || []).length > 0 && (
          <p className="field-help">
            These are the questions from {s.organization}'s application, word for word. Answer
            them here (everything saves as you type), then copy each answer into their form.
            {needsEssay && " Got an essay saved already? Start from it."}
          </p>
        )}
        <QuestionList scholarship={s} />
      </li>

      <li>
        <h2>Fill out the official application</h2>
        <p className="field-help">
          {s.organization} takes applications on their own site. Sign in there, paste in your
          answers, and upload anything it asks for.
        </p>
        {s.application_url ? (
          <a className="primary-button apply-open" href={s.application_url} target="_blank" rel="noreferrer">
            Open the official application <ExternalLink size={16} aria-hidden="true" />
          </a>
        ) : (
          <p className="field-help">No link on file. Search for it on {s.organization}'s website.</p>
        )}
      </li>

      <li>
        <h2>Mark it submitted</h2>
        {submitted ? (
          <p className="apply-success">
            <CheckCircle2 size={18} aria-hidden="true" /> Done. It's in your Saved list under Submitted.
          </p>
        ) : (
          <button type="button" className="secondary-button" onClick={markDone}>
            I submitted it
          </button>
        )}
        {error && <p className="error-text" role="alert">{error}</p>}
      </li>
    </ol>
  );
}

export default function Apply() {
  const { id } = useParams();
  const [s, setS] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getScholarship(id).then(setS).catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="screen"><p className="error-text">{error}</p></div>;
  if (!s) return <div className="screen"><p className="page-subtitle">Loading...</p></div>;

  return (
    <div className="screen apply-page">
      <Header s={s} />
      {s.hosted ? <HostedApply s={s} /> : <OutsideApply s={s} />}
    </div>
  );
}
