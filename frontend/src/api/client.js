// src/api/client.js

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
const TOKEN_KEY = "scholarmatch_token";

export function getToken() {
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

// --- Auth ---
export const signup = (email, password, consents) =>
  request("/api/auth/signup", {
    method: "POST",
    body: { email, password, ...consents },
    auth: false,
  });

export const login = (email, password) =>
  request("/api/auth/login", { method: "POST", body: { email, password }, auth: false });

export const getMe = () => request("/api/auth/me");

// --- Profile ---
export const getProfile = () => request("/api/profile");
export const updateProfile = (fields) => request("/api/profile", { method: "PUT", body: fields });

// --- Scholarships ---
export const getDeck = (limit = 25) => request(`/api/scholarships/deck?limit=${limit}`);
export const getScholarship = (id) => request(`/api/scholarships/${id}`);
export const swipeScholarship = (id, action) =>
  request(`/api/scholarships/${id}/swipe`, { method: "POST", body: { action } });

// --- Saved ---
export const getSaved = () => request("/api/saved");
export const unsaveScholarship = (id) => request(`/api/saved/${id}`, { method: "DELETE" });
export const updateScholarshipStatus = (id, status) =>
  request(`/api/saved/${id}/status`, { method: "PATCH", body: { status } });

// --- Account (privacy controls) ---
export const exportMyData = () => request("/api/account/export");
export const deleteAccount = (password) =>
  request("/api/account", { method: "DELETE", body: { password } });

// --- Stats ---
export const getStats = () => request("/api/stats");
