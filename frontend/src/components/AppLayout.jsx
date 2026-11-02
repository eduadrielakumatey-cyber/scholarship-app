// src/components/AppLayout.jsx
//
// Shell for every signed-in screen: a left sidebar with the main sections
// (modeled on study apps like OnePrep -- labels always visible, room to
// grow past four tabs) and the page content beside it.
//
// Wide screens: the sidebar is always there. Narrow screens (phones): a
// slim top bar with a menu button slides the same sidebar in from the
// left, so the nav lives in one place on every device.

import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bookmark,
  Compass,
  GraduationCap,
  Lightbulb,
  LogOut,
  Menu,
  PlayCircle,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Guide from "./guide/Guide.jsx";
import { TOUR_DONE_KEY } from "./guide/GuideTour.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Discover", Icon: Compass, end: true },
  { to: "/saved", label: "Saved", Icon: Bookmark },
  { to: "/stats", label: "Stats", Icon: BarChart3 },
  { to: "/profile", label: "Profile", Icon: GraduationCap },
  { to: "/how-it-works", label: "How it works", Icon: Lightbulb },
];

function Brand() {
  return (
    <span className="app-brand">
      Scholar<span className="brand-accent">Match</span>
    </span>
  );
}

export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const firstLinkRef = useRef(null);
  const menuButtonRef = useRef(null);

  // Close the drawer whenever the route changes (i.e. a link was tapped).
  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return undefined;
    firstLinkRef.current?.focus();
    function onKey(e) {
      if (e.key === "Escape") {
        setDrawerOpen(false);
        menuButtonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  function replayTour() {
    try {
      window.localStorage.removeItem(TOUR_DONE_KEY);
    } catch {
      // Storage blocked: Discover will offer the tour anyway.
    }
    navigate("/", { state: { tour: Date.now() } });
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className={`app-layout ${drawerOpen ? "is-drawer-open" : ""}`}>
      <header className="app-topbar">
        <button
          ref={menuButtonRef}
          type="button"
          className="app-topbar__menu"
          aria-label="Open menu"
          aria-expanded={drawerOpen}
          aria-controls="app-sidebar"
          onClick={() => setDrawerOpen(true)}
        >
          <Menu size={24} strokeWidth={2.4} />
        </button>
        <Brand />
      </header>

      <div className="app-scrim" aria-hidden="true" onClick={() => setDrawerOpen(false)} />

      <aside id="app-sidebar" className="app-sidebar">
        <div className="app-sidebar__top">
          <Brand />
          <button
            type="button"
            className="app-sidebar__close"
            aria-label="Close menu"
            onClick={() => setDrawerOpen(false)}
          >
            <X size={22} strokeWidth={2.4} />
          </button>
        </div>

        <nav className="app-nav" aria-label="Main">
          {NAV_ITEMS.map(({ to, label, Icon, end }, i) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              ref={i === 0 ? firstLinkRef : undefined}
              className={({ isActive }) => `app-nav__link ${isActive ? "is-active" : ""}`}
            >
              <span className="app-nav__icon" aria-hidden="true">
                <Icon size={20} strokeWidth={2.3} />
              </span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar__helper">
          <Guide mood="happy" size={56} />
          <div>
            <p className="app-sidebar__helper-title">Need a hand?</p>
            <button type="button" className="app-sidebar__helper-link" onClick={replayTour}>
              <PlayCircle size={16} strokeWidth={2.4} aria-hidden="true" /> Take the tour with Scout
            </button>
          </div>
        </div>

        <div className="app-sidebar__account">
          {user && <span className="app-sidebar__email">{user.email}</span>}
          <button type="button" className="app-sidebar__logout" onClick={handleLogout}>
            <LogOut size={16} strokeWidth={2.4} aria-hidden="true" /> Log out
          </button>
        </div>
      </aside>

      <main className="app-main">{children}</main>
    </div>
  );
}
