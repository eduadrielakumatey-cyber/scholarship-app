// src/components/stats/SaveRateDonut.jsx
//
// A single-ring donut built from a CSS conic-gradient -- no charting
// library needed for one ring with one real number. Used for "save rate"
// (saved vs. skipped-or-passed), the one figure on this page where a
// shape communicates faster than another number.

export default function SaveRateDonut({ percent, centerValue, centerLabel }) {
  const pct = Math.max(0, Math.min(100, percent || 0));
  const style = {
    background: `conic-gradient(var(--color-teal) ${pct}%, rgba(255, 255, 255, 0.12) ${pct}% 100%)`,
  };

  return (
    <div className="save-donut" style={style} role="img" aria-label={`${Math.round(pct)}% save rate`}>
      <div className="save-donut__hole">
        <span className="save-donut__value">{centerValue}</span>
        <span className="save-donut__label">{centerLabel}</span>
      </div>
    </div>
  );
}
