// src/components/BottomNav.jsx
//
// Fixed bottom tab bar -- the standard mobile pattern for switching
// between a small number of top-level sections (Discover / Saved /
// Profile) with one thumb-reachable tap, no hamburger menu required.

import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/", label: "Discover", icon: "🎯" },
  { to: "/saved", label: "Saved", icon: "🔖" },
  { to: "/stats", label: "Stats", icon: "📊" },
  { to: "/profile", label: "Profile", icon: "🎓" },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) => `bottom-nav__tab ${isActive ? "is-active" : ""}`}
          end={tab.to === "/"}
        >
          <span className="bottom-nav__icon" aria-hidden="true">
            {tab.icon}
          </span>
          <span className="bottom-nav__label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
