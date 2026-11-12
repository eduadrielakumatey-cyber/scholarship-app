// src/components/stats/DeadlineList.jsx
//
// The "deadlines coming up" list on the stats page -- up to 5 saved
// scholarships with the nearest deadlines, straight from the backend
// (app/services/stats.py already sorted and capped the list).

export default function DeadlineList({ deadlines }) {
  if (!deadlines || deadlines.length === 0) return null;

  return (
    <ul className="deadline-list">
      {deadlines.map((d) => (
        <li key={`${d.title}-${d.deadline}`} className="deadline-list__row">
          <div className="deadline-list__info">
            <span className="deadline-list__title">{d.title}</span>
            <span className="deadline-list__amount">{d.amount_varies ? "Varies" : `$${d.amount.toLocaleString()}`}</span>
          </div>
          <span
            className={`deadline-list__days ${
              d.days_left <= 7 ? "deadline-list__days--soon" : ""
            }`}
          >
            {d.days_left === 0 ? "Today" : `${d.days_left}d left`}
          </span>
        </li>
      ))}
    </ul>
  );
}
