// src/context/AuthContext.jsx
//
// Holds the logged-in user's profile in React state so any component can
// read "who is the current user" without prop-drilling it through every
// page. Also exposes login/signup/logout functions that update both the
// stored token (via api/client.js) and this shared state together.

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import * as api from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!api.getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  async function login(email, password) {
    const { token, user: loggedInUser } = await api.login(email, password);
    api.setToken(token);
    setUser(loggedInUser);
    return loggedInUser;
  }

  async function signup(email, password, consents) {
    const { token, user: newUser } = await api.signup(email, password, consents);
    api.setToken(token);
    setUser(newUser);
    return newUser;
  }

  async function startOnDevice(consents) {
    const { token, user: newUser } = await api.startOnDevice(consents);
    api.setToken(token);
    setUser(newUser);
    return newUser;
  }

  async function redeemLinkCode(code) {
    const { token, user: linkedUser } = await api.redeemLinkCode(code);
    api.setToken(token);
    setUser(linkedUser);
    return linkedUser;
  }

  function logout() {
    api.clearToken();
    setUser(null);
  }

  async function updateProfile(fields) {
    const updated = await api.updateProfile(fields);
    setUser(updated);
    return updated;
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, startOnDevice, redeemLinkCode, logout, updateProfile, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an <AuthProvider>");
  return ctx;
}
