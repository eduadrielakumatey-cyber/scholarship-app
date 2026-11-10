// src/components/RichEditor.jsx
//
// A small Google Docs-style editor for essays and written answers: bold,
// italic, underline, bulleted and numbered lists, undo/redo, clear
// formatting, find & replace, spell check, live word / character counts
// with the word limit, and a distraction-free focus mode.
//
// Value in and out is HTML. Older plain-text answers are converted on load.

import { useEffect, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Placeholder from "@tiptap/extension-placeholder";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Maximize2,
  Minimize2,
  Redo2,
  RemoveFormatting,
  Search,
  Underline as UnderlineIcon,
  Undo2,
} from "lucide-react";
import { countWords, textToHtml } from "../lib/text.js";

function findMatches(doc, term) {
  const out = [];
  if (!term) return out;
  const needle = term.toLowerCase();
  doc.descendants((node, pos) => {
    if (!node.isText) return;
    const hay = node.text.toLowerCase();
    let i = hay.indexOf(needle);
    while (i !== -1) {
      out.push({ from: pos + i, to: pos + i + term.length });
      i = hay.indexOf(needle, i + term.length);
    }
  });
  return out;
}

function Tool({ label, active, disabled, onClick, children }) {
  return (
    <button
      type="button"
      className={`rich-tool ${active ? "is-active" : ""}`}
      aria-label={label}
      aria-pressed={active ?? undefined}
      title={label}
      disabled={disabled}
      onMouseDown={(e) => e.preventDefault()} // keep the text selection
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function RichEditor({ value, onChange, placeholder, wordLimit, label, minHeight = 180 }) {
  const lastEmitted = useRef(null);
  const [focusMode, setFocusMode] = useState(false);
  const [findOpen, setFindOpen] = useState(false);
  const [find, setFind] = useState("");
  const [replace, setReplace] = useState("");
  const [, force] = useState(0);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: false, codeBlock: false, code: false, blockquote: false, horizontalRule: false }),
      Underline,
      Placeholder.configure({ placeholder: placeholder || "Start writing..." }),
    ],
    content: textToHtml(value || ""),
    editorProps: {
      attributes: {
        class: "rich-content",
        spellcheck: "true",
        "aria-label": label || "Your writing",
        "aria-multiline": "true",
        role: "textbox",
        style: `min-height:${minHeight}px`,
      },
    },
    onUpdate: ({ editor: ed }) => {
      const html = ed.isEmpty ? "" : ed.getHTML();
      lastEmitted.current = html;
      onChange?.(html);
    },
    onSelectionUpdate: () => force((n) => n + 1),
  });

  // Content replaced from outside (loading a saved answer, "start from a
  // saved essay"): load it without echoing it back as a change.
  useEffect(() => {
    if (!editor) return;
    const incoming = textToHtml(value || "");
    if (incoming !== lastEmitted.current && incoming !== (editor.isEmpty ? "" : editor.getHTML())) {
      editor.commands.setContent(incoming, false);
      lastEmitted.current = incoming;
    }
  }, [value, editor]);

  useEffect(() => {
    if (!focusMode) return undefined;
    const onKey = (e) => e.key === "Escape" && setFocusMode(false);
    window.addEventListener("keydown", onKey);
    document.body.classList.add("rich-focus-open");
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.classList.remove("rich-focus-open");
    };
  }, [focusMode]);

  if (!editor) return null;

  const text = editor.getText({ blockSeparator: "\n" });
  const words = countWords(text);
  const chars = text.replace(/\n/g, "").length;
  const charsNoSpaces = text.replace(/\s/g, "").length;
  const minutes = Math.max(1, Math.round(words / 200));
  const over = wordLimit && words > wordLimit;
  const matches = findOpen ? findMatches(editor.state.doc, find) : [];

  function replaceAll() {
    if (!find || matches.length === 0) return;
    const { tr } = editor.state;
    [...matches].reverse().forEach(({ from, to }) => tr.insertText(replace, from, to));
    editor.view.dispatch(tr);
  }

  function selectNext() {
    if (matches.length === 0) return;
    const { from } = editor.state.selection;
    const next = matches.find((m) => m.from > from) || matches[0];
    editor.chain().focus().setTextSelection(next).scrollIntoView().run();
  }

  const c = () => editor.chain().focus();

  return (
    <div className={`rich ${focusMode ? "rich--focus" : ""}`}>
      <div className="rich-toolbar" role="toolbar" aria-label="Formatting">
        <Tool label="Undo (Ctrl+Z)" disabled={!editor.can().undo()} onClick={() => c().undo().run()}><Undo2 size={16} /></Tool>
        <Tool label="Redo (Ctrl+Y)" disabled={!editor.can().redo()} onClick={() => c().redo().run()}><Redo2 size={16} /></Tool>
        <span className="rich-sep" />
        <Tool label="Bold (Ctrl+B)" active={editor.isActive("bold")} onClick={() => c().toggleBold().run()}><Bold size={16} /></Tool>
        <Tool label="Italic (Ctrl+I)" active={editor.isActive("italic")} onClick={() => c().toggleItalic().run()}><Italic size={16} /></Tool>
        <Tool label="Underline (Ctrl+U)" active={editor.isActive("underline")} onClick={() => c().toggleUnderline().run()}><UnderlineIcon size={16} /></Tool>
        <span className="rich-sep" />
        <Tool label="Bulleted list" active={editor.isActive("bulletList")} onClick={() => c().toggleBulletList().run()}><List size={16} /></Tool>
        <Tool label="Numbered list" active={editor.isActive("orderedList")} onClick={() => c().toggleOrderedList().run()}><ListOrdered size={16} /></Tool>
        <Tool label="Clear formatting" onClick={() => c().unsetAllMarks().clearNodes().run()}><RemoveFormatting size={16} /></Tool>
        <span className="rich-sep" />
        <Tool label="Find and replace" active={findOpen} onClick={() => setFindOpen((v) => !v)}><Search size={16} /></Tool>
        <Tool label={focusMode ? "Exit focus mode (Esc)" : "Focus mode"} active={focusMode} onClick={() => setFocusMode((v) => !v)}>
          {focusMode ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </Tool>
      </div>

      {findOpen && (
        <div className="rich-find">
          <input aria-label="Find" placeholder="Find" value={find} onChange={(e) => setFind(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), selectNext())} />
          <input aria-label="Replace with" placeholder="Replace with" value={replace} onChange={(e) => setReplace(e.target.value)} />
          <span className="rich-find__count">{find ? `${matches.length} found` : ""}</span>
          <button type="button" className="secondary-button" onClick={selectNext} disabled={!matches.length}>Next</button>
          <button type="button" className="secondary-button" onClick={replaceAll} disabled={!matches.length}>Replace all</button>
        </div>
      )}

      <EditorContent editor={editor} />

      <div className={`rich-stats ${over ? "rich-stats--over" : ""}`} aria-live="polite">
        <span>
          {words} {words === 1 ? "word" : "words"}
          {wordLimit ? ` / ${wordLimit}` : ""}
          {over ? ` (${words - wordLimit} over)` : ""}
        </span>
        <span>{chars} characters ({charsNoSpaces} without spaces)</span>
        {words > 0 && <span>~{minutes} min read</span>}
      </div>
      {wordLimit ? (
        <div className="rich-meter" aria-hidden="true">
          <span style={{ width: `${Math.min(100, (words / wordLimit) * 100)}%` }} />
        </div>
      ) : null}
    </div>
  );
}
