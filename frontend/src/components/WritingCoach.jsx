// src/components/WritingCoach.jsx
//
// Help under every essay box:
//  - Writing checks: free, instant, private (run in the browser).
//  - AI feedback: Claude reads the essay and the question and explains
//    what works and what to fix, quoting the student's own sentences. It
//    never rewrites the essay. Limited per day; hidden when it's off.

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Lightbulb, Sparkles } from "lucide-react";
import * as api from "../api/client.js";
import { countWords, htmlToText } from "../lib/text.js";
import { writingChecks } from "../lib/writingChecks.js";

let statusCache = null; // one status request per page load

const VERDICT = {
  yes: { label: "Answers the question", cls: "coach-verdict--yes" },
  partly: { label: "Partly answers the question", cls: "coach-verdict--partly" },
  no: { label: "Doesn't answer the question yet", cls: "coach-verdict--no" },
};

export default function WritingCoach({ html, question, wordLimit, scholarshipId }) {
  const text = useMemo(() => htmlToText(html), [html]);
  const checks = useMemo(() => writingChecks(text, wordLimit), [text, wordLimit]);
  const [status, setStatus] = useState(statusCache);
  const [feedback, setFeedback] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [showChecks, setShowChecks] = useState(false);

  useEffect(() => {
    if (statusCache) return;
    api.coachStatus().then((s) => {
      statusCache = s;
      setStatus(s);
    }).catch(() => {});
  }, []);

  async function ask() {
    setError(null);
    setBusy(true);
    try {
      const res = await api.coachFeedback({ text: html, question, word_limit: wordLimit || undefined, scholarship_id: scholarshipId });
      setFeedback(res.feedback);
      statusCache = { ...statusCache, remaining_today: res.remaining_today };
      setStatus(statusCache);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const words = countWords(text);
  if (words === 0) return null;
  const aiOn = status?.enabled;
  const left = status?.remaining_today ?? 0;

  return (
    <div className="coach">
      <div className="coach-bar">
        <button type="button" className="text-link-button coach-checks-toggle" onClick={() => setShowChecks((v) => !v)}>
          <Lightbulb size={15} aria-hidden="true" />{" "}
          {checks.length === 0 ? "Writing checks: looks clean" : `${checks.length} writing ${checks.length === 1 ? "tip" : "tips"}`}
          {checks.length > 0 && (showChecks ? " (hide)" : " (show)")}
        </button>
        {aiOn && (
          <button type="button" className="secondary-button coach-ai" onClick={ask} disabled={busy || left <= 0 || words < 40}
            title={words < 40 ? "Write at least 40 words first" : ""}>
            <Sparkles size={15} aria-hidden="true" />{" "}
            {busy ? "Reading your essay..." : feedback ? "Get new feedback" : "Get AI feedback"}
            <span className="coach-left">{left} left today</span>
          </button>
        )}
      </div>

      {showChecks && checks.length > 0 && (
        <ul className="coach-checks">
          {checks.map((c, i) => (
            <li key={i}>
              <strong>{c.title}</strong>
              {c.quote && <q>{c.quote}</q>}
              <span>{c.detail}</span>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="error-text" role="alert">{error}</p>}

      {feedback && (
        <div className="coach-feedback" aria-live="polite">
          <p className="coach-summary">{feedback.summary}</p>
          {feedback.answers_question && (
            <p className={`coach-verdict ${VERDICT[feedback.answers_question.verdict]?.cls || ""}`}>
              <strong>{VERDICT[feedback.answers_question.verdict]?.label}:</strong> {feedback.answers_question.explanation}
            </p>
          )}
          {feedback.strengths?.length > 0 && (
            <>
              <h4>What's working</h4>
              <ul>
                {feedback.strengths.map((s, i) => (
                  <li key={i}>
                    <CheckCircle2 size={14} aria-hidden="true" /> {s.quote && <q>{s.quote}</q>} {s.why}
                  </li>
                ))}
              </ul>
            </>
          )}
          {feedback.improvements?.length > 0 && (
            <>
              <h4>What to work on</h4>
              <ol>
                {feedback.improvements.map((s, i) => (
                  <li key={i}>
                    {s.quote && <q>{s.quote}</q>}
                    <strong>{s.issue}</strong> {s.suggestion}
                  </li>
                ))}
              </ol>
            </>
          )}
          <p className="coach-note">AI feedback can be wrong. It's advice, and the words should stay yours.</p>
        </div>
      )}
    </div>
  );
}
