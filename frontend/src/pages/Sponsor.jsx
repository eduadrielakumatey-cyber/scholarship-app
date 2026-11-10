// src/pages/Sponsor.jsx
//
// /sponsor -- a local business, club or family posts a scholarship on
// ScholarMatch. Students apply inside the app; the sponsor gets a private
// link to read applications and pick winners. Listings go live only after
// ScholarMatch approves them. ScholarMatch never handles the money.

import { useState } from "react";
import { Link } from "react-router-dom";
import { Copy } from "lucide-react";
import * as api from "../api/client.js";
import LegalFooter from "../components/LegalFooter.jsx";

const GRADES = [
  ["12", "High school seniors"],
  ["college_1", "College freshmen"],
  ["college_2", "College sophomores"],
  ["college_3", "College juniors"],
  ["college_4", "College seniors"],
  ["college_5plus", "Graduate students"],
];

export default function Sponsor() {
  const [form, setForm] = useState({
    title: "", organization: "", description: "", essay_prompt: "",
    amount: "", num_awards: "1", deadline: "", min_gpa: "",
    sponsor_name: "", sponsor_email: "", maryland_only: true,
  });
  const [grades, setGrades] = useState(["12"]);
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [link, setLink] = useState(null);
  const [copied, setCopied] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { review_token } = await api.postSponsorScholarship({
        title: form.title,
        organization: form.organization,
        description: form.description,
        essay_prompt: form.essay_prompt,
        amount: Number(form.amount),
        num_awards: Number(form.num_awards || 1),
        deadline: form.deadline,
        min_gpa: form.min_gpa ? Number(form.min_gpa) : null,
        grade_levels: grades,
        states: form.maryland_only ? ["MD"] : [],
        sponsor_name: form.sponsor_name,
        sponsor_email: form.sponsor_email,
        agree,
      });
      setLink(`${window.location.origin}/review/${review_token}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (link) {
    return (
      <div className="start-page">
        <div className="screen">
          <h1 className="page-title">Thanks! Save this link</h1>
          <p className="page-subtitle">
            We'll review your scholarship, usually within a couple of days, and it goes live once
            approved. This private link is where you'll read applications and pick a winner.
            <strong> It's shown only once, so bookmark it or email it to yourself now.</strong>
          </p>
          <div className="sponsor-link">
            <code>{link}</code>
            <button type="button" className="secondary-button"
              onClick={() => navigator.clipboard.writeText(link).then(() => setCopied(true)).catch(() => {})}>
              <Copy size={16} aria-hidden="true" /> {copied ? "Copied" : "Copy link"}
            </button>
          </div>
          <p className="field-help">Anyone with this link can see the applications, so keep it private.</p>
          <Link className="secondary-button" to={link.replace(window.location.origin, "")}>Open my review page</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="start-page">
      <div className="screen">
        <Link to="/" className="text-link-button">← ScholarMatch</Link>
        <h1 className="page-title" style={{ marginTop: 12 }}>Offer a scholarship</h1>
        <p className="page-subtitle">
          For local businesses, clubs, families and alumni. Post it here, Maryland students apply
          right in the app, and you pick the winner from a private page. Free. You pay the winner
          (or their school) directly.
        </p>

        <form onSubmit={submit}>
          <div className="field-group">
            <label htmlFor="sp-title">Scholarship name</label>
            <input id="sp-title" required maxLength={160} placeholder="e.g. Waldorf Hardware Trades Scholarship"
              value={form.title} onChange={set("title")} />
          </div>
          <div className="field-group">
            <label htmlFor="sp-org">Who's offering it</label>
            <input id="sp-org" required maxLength={160} placeholder="Business, club or family name"
              value={form.organization} onChange={set("organization")} />
          </div>
          <div className="field-group">
            <label htmlFor="sp-desc">Who it's for and what it pays for</label>
            <textarea id="sp-desc" required rows={4} minLength={40} maxLength={2000}
              placeholder="e.g. For Charles County seniors going into a trade program. Paid to the school."
              value={form.description} onChange={set("description")} />
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="sp-amount">Award ($)</label>
              <input id="sp-amount" type="number" required min={50} max={100000} value={form.amount} onChange={set("amount")} />
            </div>
            <div className="field-group">
              <label htmlFor="sp-num">Number of winners</label>
              <input id="sp-num" type="number" required min={1} max={100} value={form.num_awards} onChange={set("num_awards")} />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="sp-deadline">Deadline</label>
              <input id="sp-deadline" type="date" required value={form.deadline} onChange={set("deadline")} />
            </div>
            <div className="field-group">
              <label htmlFor="sp-gpa">Minimum GPA (optional)</label>
              <input id="sp-gpa" type="number" step="0.1" min={0} max={5} value={form.min_gpa} onChange={set("min_gpa")} />
            </div>
          </div>

          <fieldset className="field-group field-group--fieldset">
            <legend>Who can apply</legend>
            <div className="chip-row">
              {GRADES.map(([value, label]) => (
                <button key={value} type="button" className="chip" aria-pressed={grades.includes(value)}
                  onClick={() => setGrades(grades.includes(value) ? grades.filter((g) => g !== value) : [...grades, value])}>
                  {label}
                </button>
              ))}
            </div>
            <label className="consent-check">
              <input type="checkbox" checked={form.maryland_only}
                onChange={(e) => setForm({ ...form, maryland_only: e.target.checked })} />
              <span>Maryland students only</span>
            </label>
          </fieldset>

          <div className="field-group">
            <label htmlFor="sp-prompt">Essay question (optional, keep it short)</label>
            <textarea id="sp-prompt" rows={2} maxLength={1000}
              placeholder="e.g. In 250 words, tell us what trade you want to learn and why."
              value={form.essay_prompt} onChange={set("essay_prompt")} />
          </div>

          <div className="field-row">
            <div className="field-group">
              <label htmlFor="sp-name">Your name</label>
              <input id="sp-name" required autoComplete="name" value={form.sponsor_name} onChange={set("sponsor_name")} />
            </div>
            <div className="field-group">
              <label htmlFor="sp-email">Your email (not shown to students)</label>
              <input id="sp-email" type="email" required autoComplete="email" value={form.sponsor_email} onChange={set("sponsor_email")} />
            </div>
          </div>

          <label className="consent-check">
            <input type="checkbox" required checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            <span>
              I'll pay the winner(s) as described, use applicants' information only to choose and
              contact winners, and never charge students to apply. I agree to the{" "}
              <Link to="/terms">Terms</Link>.
            </span>
          </label>

          {error && <p className="error-text" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={busy || grades.length === 0}>
            {busy ? "Sending..." : "Submit for review"}
          </button>
        </form>
        <LegalFooter />
      </div>
    </div>
  );
}
