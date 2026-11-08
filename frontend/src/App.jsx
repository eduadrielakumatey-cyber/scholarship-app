// src/App.jsx
//
// Top-level route table. Wraps everything in <AuthProvider> so any page
// can call useAuth(), and gates the main app behind <RequireAuth> so a
// visitor with no profile on this device is sent to the homepage instead
// of hitting a broken page. There's no sign-up: /start makes a profile
// tied to this device; /link opens it on another device with a one-time code. /login stays only for older email accounts.

import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import Login from "./pages/Login.jsx";
import Landing from "./pages/Landing.jsx";
import ProfileSetup from "./pages/ProfileSetup.jsx";
import Discover from "./pages/Discover.jsx";
import Saved from "./pages/Saved.jsx";
import Detail from "./pages/Detail.jsx";
import Stats from "./pages/Stats.jsx";
import HowItWorks from "./pages/HowItWorks.jsx";
import LinkDevice from "./pages/LinkDevice.jsx";
import { Privacy, Terms, Cookies, Licenses } from "./pages/Legal.jsx";
import StorageNotice from "./components/StorageNotice.jsx";
import AppLayout from "./components/AppLayout.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="screen" />;
  if (!user) return <Navigate to="/" replace />;
  return <AppLayout>{children}</AppLayout>;
}

// The no-sign-up start screen. Someone who already has a profile on this
// device goes straight to their deck.
function Start() {
  const { user, loading } = useAuth();
  if (loading) return <div className="screen" />;
  if (user) return <Navigate to="/" replace />;
  return (
    <div className="start-page">
      <ProfileSetup />
    </div>
  );
}

// Old "/login?mode=signup" links (shared posts, bookmarks) go to /start.
function LoginRoute() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("mode") === "signup") return <Navigate to="/start" replace />;
  return <Login />;
}

// "/" is the public homepage for visitors and the swipe deck once signed in.
function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="screen" />;
  if (!user) return <Landing />;
  return (
    <AppLayout>
      <Discover />
    </AppLayout>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/start" element={<Start />} />
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/link" element={<LinkDevice />} />
      {/* Policies are public: people must be able to read them before signing up. */}
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/cookies" element={<Cookies />} />
      <Route path="/licenses" element={<Licenses />} />
      <Route path="/" element={<Home />} />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfileSetup />
          </RequireAuth>
        }
      />
      <Route
        path="/saved"
        element={
          <RequireAuth>
            <Saved />
          </RequireAuth>
        }
      />
      <Route
        path="/scholarship/:id"
        element={
          <RequireAuth>
            <Detail />
          </RequireAuth>
        }
      />
      <Route
        path="/stats"
        element={
          <RequireAuth>
            <Stats />
          </RequireAuth>
        }
      />
      <Route
        path="/how-it-works"
        element={
          <RequireAuth>
            <HowItWorks />
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <AuthProvider>
        <AppRoutes />
        <StorageNotice />
      </AuthProvider>
    </div>
  );
}
