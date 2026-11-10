// src/pages/Essays.jsx
//
// The student's essay library: write once, reuse for every scholarship.

import EssayEditor from "../components/EssayEditor.jsx";

export default function Essays() {
  return (
    <div className="screen">
      <h1 className="page-title">My essays</h1>
      <p className="page-subtitle">
        Most scholarships ask the same few questions: your goals, leadership, a challenge you
        faced, why your major. Write each one once here and reuse it. Everything saves as you type,
        and you get instant writing tips (plus AI feedback when it's on) right under your essay.
      </p>
      <EssayEditor allowDelete />
    </div>
  );
}
