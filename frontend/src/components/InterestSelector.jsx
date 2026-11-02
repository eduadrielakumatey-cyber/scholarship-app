// src/components/InterestSelector.jsx
//
// Extends the plain chip-toggle pattern (still used for demographics) with
// a way to add interests that aren't in the predefined list. Custom
// interests are stored in exactly the same `interests` array as the
// predefined ones -- there's no separate "custom" field anywhere -- so
// they flow through profile save, matching, and scoring for free. This
// component's only job is collecting them with the same chip look/feel
// instead of a bolted-on text box.

import { useRef, useState } from "react";
import { normalizeInterest, parseCustomInterests } from "../utils/interests.js";

export default function InterestSelector({ options, selected, onChange }) {
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState("");
  const inputRef = useRef(null);

  const optionSet = new Set(options.map(normalizeInterest));
  const customInterests = selected.filter((v) => !optionSet.has(normalizeInterest(v)));

  function toggleOption(option) {
    const norm = normalizeInterest(option);
    const has = selected.some((v) => normalizeInterest(v) === norm);
    onChange(has ? selected.filter((v) => normalizeInterest(v) !== norm) : [...selected, norm]);
  }

  function removeCustom(value) {
    const norm = normalizeInterest(value);
    onChange(selected.filter((v) => normalizeInterest(v) !== norm));
  }

  function commitDraft() {
    const additions = parseCustomInterests(draft, selected);
    if (additions.length > 0) {
      onChange([...selected, ...additions]);
    }
    setDraft("");
  }

  function openAdder() {
    setAdding(true);
    // Focus after the input actually mounts.
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitDraft();
    } else if (e.key === "Escape") {
      setDraft("");
      setAdding(false);
    }
  }

  function handleBlur() {
    commitDraft();
    setAdding(false);
  }

  return (
    <div className="chip-row">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className="chip"
          aria-pressed={selected.some((v) => normalizeInterest(v) === normalizeInterest(option))}
          onClick={() => toggleOption(option)}
        >
          {option}
        </button>
      ))}

      {customInterests.map((value) => (
        <span key={value} className="chip chip--custom">
          {value}
          <button
            type="button"
            className="chip__remove"
            aria-label={`Remove ${value}`}
            onClick={() => removeCustom(value)}
          >
            ×
          </button>
        </span>
      ))}

      {adding ? (
        <span className="chip-input-row">
          <input
            ref={inputRef}
            type="text"
            className="chip-input"
            aria-label="Add your own interests, separated by commas"
            placeholder="e.g. robotics, embedded systems"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
          />
          {/* Enter (or clicking away) also commits -- this button exists so
              the action isn't hidden behind a keyboard shortcut alone.
              onMouseDown preventDefault stops the input's blur from firing
              (and closing the adder) before the click itself registers. */}
          <button
            type="button"
            className="chip chip--confirm"
            onMouseDown={(e) => e.preventDefault()}
            onClick={commitDraft}
          >
            Add
          </button>
        </span>
      ) : (
        <button type="button" className="chip chip--add" onClick={openAdder}>
          + Add your own
        </button>
      )}
    </div>
  );
}
