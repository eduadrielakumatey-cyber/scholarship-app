// src/components/stats/StatTile.jsx
//
// One big number + a short label. The entire "Stats for Idiots" page is
// built out of these plus a couple of small shapes below -- deliberately
// not a data-grid/table, since the goal is "readable in ~10 seconds."

export default function StatTile({ value, label, accent }) {
  return (
    <div className={`stat-tile ${accent ? `stat-tile--${accent}` : ""}`}>
      <span className={`stat-tile__value ${accent ? `stat-tile__value--${accent}` : ""}`}>
        {value}
      </span>
      <span className="stat-tile__label">{label}</span>
    </div>
  );
}
