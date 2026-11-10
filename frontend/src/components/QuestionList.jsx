// src/components/QuestionList.jsx
//
// Every question on a scholarship's official application, word for word,
// with a place to answer each one. Written questions get the full editor
// (formatting, counts, find & replace, focus mode) plus writing checks and
// AI feedback; yes/no, short and reference questions get simple inputs.
// Answers save as you type, each has a Copy button for pasting into the
// official form, and "Copy all answers" grabs everything at once. Essay
// questions can start from an essay already in the student's library.

import { useEffect, useRef, useState } from "react";
import { Check, Copy, FileUp, UserRound } from "lucide-react";
import * as api from "../api/client.js";
import RichEditor from "./RichEditor.jsx";
import WritingCoach from "./WritingCoach.jsx";
import { copyRich, htmlToText } from "../lib/text.js";

const SAVE_DELAY_MS = 700;

function CopyButton({ value, label = "Copy", rich = false }) {
  const [done, setDone] = useState(false);
  const plain = rich ? htmlToText(value) : (value || "").trim();
  async function copy() {
    try {
      if (rich) await copyRich(value);
      else await navigator.clipboard.writeText(plain);
      setDone(true);
      setTimeout(() => setDone(false), 1800);
    } catch {
      // clipboard blocked: nothing to do
    }
  }
  return (
    <button type="button" className="secondary-button q-copy" disabled={!plain} onClick={copy}>
      {done ? <Check size={15} aria-hidden="true" /> : <Copy size={15} aria-hidden="true" />} {done ? "Copied" : label}
    </button>
  );
}

function SaveStatus({ status }) {
  return (
    <span className="q-save">
      {status === "saving" ? "Saving..." : status === "saved" ? "Saved" : status === "error" ? "Not saved, try again" : ""}
    </span>
  );
}

function Question({ q, index, value, essays, onChange, status, scholarshipId }) {
  const id = `q-${q.key}`;
  // A yes/no answer is stored as "Yes" or "No", plus any details on the
  // following lines ("Yes\nI'll graduate from Fort Hill in June").
  const lines = (value || "").split("\n");
  const ynValue = lines[0] === "Yes" || lines[0] === "No" ? lines[0] : "";
  const followText = ynValue ? lines.slice(1).join("\n") : (value || "").replace(/^\n/, "");
  const yesNo = (choice, details) => (details ? `${choice}\n${details}` : choice);

  return (
    <li className={`q q--${q.kind}`}>
      <label htmlFor={id} className="q-text">
        <span className="q-num">{index + 1}</span>
        <span>
          {q.source === "requirements" && <em className="q-from">From the requirements: </em>}
          {q.text}
        </span>
      </label>

      {q.kind === "upload" && (
        <p className="q-note">
          <FileUp size={16} aria-hidden="true" /> You'll upload this on their official form. Get the file ready now.
        </p>
      )}

      {q.kind === "reference" && (
        <p className="q-note">
          <UserRound size={16} aria-hidden="true" /> Ask your recommender early. Note their name and contact here.
        </p>
      )}

      {q.kind === "written" && (
        <>
          {essays.length > 0 && (
            <select
              className="q-essay-pick"
              aria-label="Start from a saved essay"
              value=""
              onChange={(e) => {
                const essay = essays.find((x) => String(x.id) === e.target.value);
                if (essay && (!htmlToText(value) || window.confirm("Replace what you've written with this saved essay?"))) {
                  onChange(essay.body);
                }
              }}
            >
              <option value="">Start from a saved essay...</option>
              {essays.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.title} ({e.word_count} words)
                </option>
              ))}
            </select>
          )}
          <RichEditor
            value={value}
            onChange={onChange}
            wordLimit={q.word_limit}
            label={q.text}
            placeholder="Write your answer here. It saves as you type."
          />
          <div className="q-foot">
            <SaveStatus status={status} />
            <CopyButton value={value} rich />
          </div>
          <WritingCoach html={value} question={q.text} wordLimit={q.word_limit} scholarshipId={scholarshipId} />
        </>
      )}

      {q.kind === "yesno" && (
        <div className="q-yesno" role="group" aria-label="Your answer">
          {["Yes", "No"].map((opt) => (
            <button key={opt} type="button" className="chip" aria-pressed={ynValue === opt}
              onClick={() => onChange(yesNo(opt, followText))}>
              {opt}
            </button>
          ))}
        </div>
      )}

      {(q.kind === "short" || q.kind === "reference" || (q.kind === "yesno" && q.follow_up)) && (
        <textarea
          id={id}
          rows={2}
          placeholder={q.kind === "yesno" ? "If yes, add the details here" : q.kind === "reference" ? "Name, email or phone" : "Your answer"}
          spellCheck
          value={q.kind === "yesno" ? followText : value || ""}
          onChange={(e) =>
            onChange(q.kind === "yesno" ? (ynValue ? yesNo(ynValue, e.target.value) : `\n${e.target.value}`) : e.target.value)
          }
        />
      )}

      {q.kind !== "upload" && q.kind !== "written" && (
        <div className="q-foot">
          <SaveStatus status={status} />
          <CopyButton value={value} />
        </div>
      )}
    </li>
  );
}

export default function QuestionList({ scholarship }) {
  const questions = scholarship.questions || [];
  const [answers, setAnswers] = useState({});
  const [status, setStatus] = useState({});
  const [essays, setEssays] = useState([]);
  const timers = useRef({});
  const latest = useRef({});

  useEffect(() => {
    api.getAnswers(scholarship.id).then(({ answers: a }) => setAnswers(a || {})).catch(() => {});
    api.getEssays().then(({ results }) => setEssays(results)).catch(() => {});
  }, [scholarship.id]);

  useEffect(() => {
    const pending = timers.current;
    return () => Object.values(pending).forEach(clearTimeout);
  }, []);

  function change(key, body) {
    setAnswers((a) => ({ ...a, [key]: body }));
    latest.current[key] = body;
    clearTimeout(timers.current[key]);
    timers.current[key] = setTimeout(async () => {
      setStatus((s) => ({ ...s, [key]: "saving" }));
      try {
        await api.saveAnswer(scholarship.id, key, latest.current[key]);
        setStatus((s) => ({ ...s, [key]: "saved" }));
      } catch {
        setStatus((s) => ({ ...s, [key]: "error" }));
      }
    }, SAVE_DELAY_MS);
  }

  if (questions.length === 0) {
    return (
      <p className="field-help">
        Their listing doesn't ask any extra questions, so there's nothing to write. Just fill out
        their form.
      </p>
    );
  }

  const answered = questions.filter((q) => q.kind === "upload" || htmlToText(answers[q.key]).trim()).length;
  const allText = questions
    .filter((q) => q.kind !== "upload")
    .map((q, i) => `${i + 1}. ${q.text}\n${htmlToText(answers[q.key]).trim() || "(no answer yet)"}`)
    .join("\n\n");

  return (
    <div className="q-list">
      <div className="q-progress">
        <span>
          {answered} of {questions.length} ready
        </span>
        <CopyButton value={allText} label="Copy all answers" />
      </div>
      <ol>
        {questions.map((q, i) => (
          <Question
            key={q.key}
            q={q}
            index={i}
            value={answers[q.key] || ""}
            essays={essays}
            status={status[q.key]}
            scholarshipId={scholarship.id}
            onChange={(body) => change(q.key, body)}
          />
        ))}
      </ol>
    </div>
  );
}
