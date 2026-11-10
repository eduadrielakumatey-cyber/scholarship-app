// src/lib/text.js
//
// Essays and answers are stored as editor HTML (bold, lists...). Official
// application forms mostly take plain text, so these helpers turn HTML into
// clean plain text for word counts, copying and the writing checks, and
// turn older plain-text answers into HTML for the editor.

export function htmlToText(html) {
  if (!html) return "";
  if (!/^\s*</.test(html)) return html; // already plain text
  const doc = new DOMParser().parseFromString(html, "text/html");
  const blocks = [];
  doc.body.childNodes.forEach((node) => {
    if (node.nodeName === "UL" || node.nodeName === "OL") {
      let n = 1;
      node.querySelectorAll(":scope > li").forEach((li) => {
        blocks.push(`${node.nodeName === "OL" ? `${n++}.` : "•"} ${li.textContent.trim()}`);
      });
    } else {
      const t = node.textContent.trim();
      if (t) blocks.push(t);
    }
  });
  return blocks.join("\n\n");
}

export function textToHtml(text) {
  if (!text) return "";
  if (/^\s*</.test(text)) return text; // already HTML
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return text
    .split(/\n{2,}|\n/)
    .map((p) => `<p>${esc(p)}</p>`)
    .join("");
}

export function countWords(text) {
  const t = (text || "").trim();
  return t ? t.split(/\s+/).length : 0;
}

// Copies with formatting where the destination supports it (Google Docs,
// Word, rich web editors) and as plain text everywhere else.
export async function copyRich(html) {
  const text = htmlToText(html);
  try {
    if (window.ClipboardItem && /^\s*</.test(html || "")) {
      await navigator.clipboard.write([
        new window.ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([text], { type: "text/plain" }),
        }),
      ]);
      return true;
    }
  } catch {
    // fall through to plain text
  }
  await navigator.clipboard.writeText(text);
  return true;
}
