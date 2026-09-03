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
    </Routes>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </div>
  );
}
