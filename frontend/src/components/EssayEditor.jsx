// src/components/EssayEditor.jsx
//
// Write an essay once, reuse it everywhere. Essays live in the student's
// library (saved to their profile as they type), so the "leadership" essay
// written for one scholarship is one tap away for the next five. Used on
// the Apply page and the Essays page.

import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Copy, Plus, Trash2 } from "lucide-react";
import * as api from "../api/client.js";
import RichEditor from "./RichEditor.jsx";
import WritingCoach from "./WritingCoach.jsx";
import { copyRich, countWords, htmlToText } from "../lib/text.js";

const SAVE_DELAY_MS = 800;

// Essay bodies are editor HTML; counts use the plain text.
export function wordCount(text) {
  return countWords(htmlToText(text));
}

export default function EssayEditor({ prompt, onTextChange, allowDelete = false, autoFocus = false }) {
  const [essays, setEssays] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved | error
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);
  const timer = useRef(null);
  const pendingSave = useRef(null); // the save waiting on the typing pause
  const chain = useRef(Promise.resolve()); // saves run one at a time
  // Each opened essay gets a "session" number; a save always goes to the
  // essay of the session it was typed in, even if the student has switched
  // to another essay by the time it runs. A new essay's id is filled in
  // once its first save creates it.
  const session = useRef(0);
  const sessionIds = useRef(new Map());

  const flush = useCallback(() => {
    clearTimeout(timer.current);
    if (pendingSave.current) {
      const run = pendingSave.current;
      pendingSave.current = null;
      chain.current = chain.current.then(run);
    }
  }, []);

  const select = useCallback(
    (essay) => {
      flush();
      session.current += 1;
      sessionIds.current.set(session.current, essay?.id ?? null);
      setCurrentId(essay?.id ?? null);
      setTitle(essay?.title ?? "");
      setBody(essay?.body ?? "");
      setSaveState("idle");
    },
    [flush]
  );

  useEffect(() => {
    api
      .getEssays()
      .then(({ results }) => {
        setEssays(results);
        select(results[0] || null);
      })
      .catch((err) => setError(err.message));
  }, [select]);

  useEffect(() => {
    onTextChange?.(body);
  }, [body, onTextChange]);

  async function save(fields, sid) {
    const isCurrent = sid === session.current;
    if (isCurrent) setSaveState("saving");
    try {
      const id = sessionIds.current.get(sid);
      let saved;
      if (id) {
        saved = await api.updateEssay(id, fields);
      } else {
        saved = await api.createEssay(fields);
        sessionIds.current.set(sid, saved.id);
        if (sid === session.current) setCurrentId(saved.id);
      }
      setEssays((list) => [saved, ...list.filter((e) => e.id !== saved.id)]);
      if (sid === session.current) setSaveState("saved");
    } catch (err) {
      if (sid === session.current) setSaveState("error");
      setError(err.message);
    }
  }

  function scheduleSave(nextTitle, nextBody) {
    const sid = session.current;
    const fields = { title: nextTitle.trim() || "Untitled essay", body: nextBody };
    pendingSave.current = () => save(fields, sid);
    clearTimeout(timer.current);
    timer.current = setTimeout(flush, SAVE_DELAY_MS);
  }

  // Leaving the page saves whatever was typed in the last moment.
  useEffect(() => () => flush(), [flush]);

  function startNew() {
    select(null);
  }

  async function remove() {
    if (!currentId) return;
    clearTimeout(timer.current);
    pendingSave.current = null;
    try {
      await api.deleteEssay(currentId);
      const rest = essays.filter((e) => e.id !== currentId);
      setEssays(rest);
      select(rest[0] || null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function copy() {
    try {
      await copyRich(body);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Couldn't copy. Select the text and copy it yourself.");
    }
  }

  const words = wordCount(body);

  return (
    <div className="essay-editor">
      {prompt && (
        <blockquote className="essay-editor__prompt">
          <span>Essay question</span>
          {prompt}
        </blockquote>
      )}

      <div className="essay-editor__bar">
        <select
          aria-label="Choose a saved essay"
          value={currentId ?? ""}
          onChange={(e) => {
            clearTimeout(timer.current);
            select(essays.find((x) => String(x.id) === e.target.value) || null);
          }}
        >
          <option value="">{currentId ? "New essay" : "New essay (not saved yet)"}</option>
          {essays.map((e) => (
            <option key={e.id} value={e.id}>
              {e.title} ({e.word_count} words)
            </option>
          ))}
        </select>
        <button type="button" className="secondary-button" onClick={startNew}>
          <Plus size={16} aria-hidden="true" /> New
        </button>
        {allowDelete && currentId && (
          <button type="button" className="secondary-button secondary-button--danger" onClick={remove}>
            <Trash2 size={16} aria-hidden="true" /> Delete
          </button>
        )}
      </div>

      <div className="field-group">
        <label htmlFor="essay-title">Essay name (just for you)</label>
        <input
          id="essay-title"
          placeholder="e.g. Leadership, Why nursing, A challenge I faced"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            scheduleSave(e.target.value, body);
          }}
        />
      </div>

      <RichEditor
        value={body}
        label="Your essay"
        minHeight={280}
        placeholder="Write here. It saves as you type, and you can reuse it for other scholarships."
        onChange={(html) => {
          setBody(html);
          scheduleSave(title, html);
        }}
      />

      <div className="essay-editor__footer">
        <span>
          {words > 0 && (saveState === "saving" ? "Saving..." : saveState === "error" ? "Not saved" : "Saved")}
        </span>
        <button type="button" className="secondary-button" onClick={copy} disabled={!body}>
          {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}{" "}
          {copied ? "Copied" : "Copy essay"}
        </button>
      </div>

      <WritingCoach html={body} question={prompt} />

      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
