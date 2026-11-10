// src/lib/writingChecks.js
//
// Free, instant writing checks that run in the browser (nothing is sent
// anywhere). Each finding quotes the spot it's about so the student can
// find it. Tuned for scholarship essays: be specific, be concise, sound
// like yourself, answer the question within the limit.

const CLICHES = [
  "ever since i was young", "ever since i was a child", "since i was little", "for as long as i can remember",
  "make a difference", "make the world a better place", "dictionary defines", "according to webster",
  "at the end of the day", "think outside the box", "hard work pays off", "follow my dreams", "follow my passion",
  "change the world", "give back to my community", "i have always been passionate", "in today's society",
  "it is important to note", "last but not least", "the sky is the limit", "everything happens for a reason",
  "i am a hard worker", "comfort zone", "words cannot describe", "a dream come true", "life-changing experience",
];
const FILLERS = ["very", "really", "just", "actually", "basically", "literally", "things", "stuff", "a lot", "kind of", "sort of", "extremely", "truly", "definitely"];
const WEAK_OPENERS = ["in this essay", "this essay will", "i am writing", "my name is", "hello, my name"];
const PASSIVE = /\b(am|is|are|was|were|be|been|being)\s+(\w+ed|given|taken|made|done|shown|known|seen|told|chosen|written)\b/gi;
const STOP = new Set(("the a an and or but of to in on for with at by from as is are was were be been it this that these those i me my we our you your he she they them his her their " +
  "have has had do did not no so if then than too also can could would should will just very really about into over more most some any all").split(" "));

function sentences(text) {
  return (text.match(/[^.!?\n]+[.!?]*/g) || []).map((s) => s.trim()).filter(Boolean);
}

function snippet(s, max = 70) {
  return s.length > max ? `${s.slice(0, max).trim()}...` : s;
}

export function writingChecks(text, wordLimit) {
  const out = [];
  const t = (text || "").trim();
  if (!t) return out;
  const lower = t.toLowerCase();
  const words = t.split(/\s+/);
  const sents = sentences(t);

  if (wordLimit) {
    if (words.length > wordLimit) {
      out.push({ kind: "limit", title: `${words.length - wordLimit} words over the limit`, detail: `The limit is ${wordLimit}. Many forms cut you off or reject long answers, so trim the weakest sentences.` });
    } else if (words.length < wordLimit * 0.6 && words.length > 30) {
      out.push({ kind: "limit", title: "Room to say more", detail: `You've used ${words.length} of ${wordLimit} words. A specific example or detail could make it stronger.` });
    }
  }

  for (const opener of WEAK_OPENERS) {
    if (lower.startsWith(opener)) {
      out.push({ kind: "opening", title: "Start with something specific", detail: "Readers skim dozens of essays. Opening with a moment, a detail or a question grabs them faster than introducing the essay or yourself.", quote: snippet(sents[0] || t) });
      break;
    }
  }

  for (const c of CLICHES) {
    const i = lower.indexOf(c);
    if (i !== -1) {
      out.push({ kind: "cliche", title: "Common phrase", detail: "Committees see this a lot. Replace it with something only you could say: what actually happened, or what you actually did.", quote: t.slice(i, i + c.length) });
    }
  }

  sents.forEach((s) => {
    const n = s.split(/\s+/).length;
    if (n > 35) out.push({ kind: "long", title: `Long sentence (${n} words)`, detail: "Try splitting it in two. Shorter sentences are easier to follow.", quote: snippet(s) });
  });

  const fillerHits = [];
  for (const f of FILLERS) {
    const re = new RegExp(`\\b${f.replace(/ /g, "\\s+")}\\b`, "gi");
    const m = t.match(re);
    if (m) fillerHits.push(`"${f}" ×${m.length}`);
  }
  if (fillerHits.length) {
    out.push({ kind: "filler", title: "Filler words", detail: `These rarely add meaning: ${fillerHits.join(", ")}. Cutting them makes your writing sharper and frees up words.` });
  }

  const passive = [...t.matchAll(PASSIVE)].slice(0, 3);
  passive.forEach((m) => {
    out.push({ kind: "passive", title: "Possible passive voice", detail: "Saying who did what (\"I organized...\" instead of \"...was organized\") sounds more confident.", quote: m[0] });
  });

  const counts = {};
  words.forEach((w) => {
    const k = w.toLowerCase().replace(/[^a-z']/g, "");
    if (k.length > 3 && !STOP.has(k)) counts[k] = (counts[k] || 0) + 1;
  });
  const repeated = Object.entries(counts)
    .filter(([, n]) => n >= Math.max(4, Math.round(words.length / 60)))
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  if (repeated.length) {
    out.push({ kind: "repeat", title: "Repeated words", detail: `${repeated.map(([w, n]) => `"${w}" ×${n}`).join(", ")}. Varying them keeps the reader's attention.` });
  }

  const starts = {};
  sents.forEach((s) => {
    const first = s.split(/\s+/)[0]?.toLowerCase().replace(/[^a-z]/g, "");
    if (first) starts[first] = (starts[first] || 0) + 1;
  });
  const iStarts = starts.i || 0;
  if (sents.length >= 5 && iStarts / sents.length > 0.4) {
    out.push({ kind: "variety", title: `${iStarts} of ${sents.length} sentences start with "I"`, detail: "Mixing up how sentences begin makes the essay flow better." });
  }

  if ((t.match(/!/g) || []).length > 2) {
    out.push({ kind: "tone", title: "Lots of exclamation points", detail: "Let your examples show the excitement instead. One at most usually reads best." });
  }
  return out;
}
