// src/App.jsx
//
// Top-level route table. Wraps everything in <AuthProvider> so any page
// can call useAuth(), and gates the main app behind <RequireAuth> so a
// logged-out visitor is sent to /login instead of hitting a broken
// authenticated page.

import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import Login from "./pages/Login.jsx";
import ProfileSetup from "./pages/ProfileSetup.jsx";
import Discover from "./pages/Discover.jsx";
import Saved from "./pages/Saved.jsx";
import Detail from "./pages/Detail.jsx";
import Stats from "./pages/Stats.jsx";
import HowItWorks from "./pages/HowItWorks.jsx";
import { Privacy, Terms, Cookies, Licenses } from "./pages/Legal.jsx";
import StorageNotice from "./components/StorageNotice.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="screen" />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* Policies are public: people must be able to read them before signing up. */}
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/cookies" element={<Cookies />} />
      <Route path="/licenses" element={<Licenses />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Discover />
          </RequireAuth>
        }
      />
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
