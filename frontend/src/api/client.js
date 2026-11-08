// src/api/client.js

// Without an override, talk to port 5000 on whatever host served the page:
// localhost on this computer, or the computer's current Wi-Fi address when
// testing from a phone -- so a changed network IP never breaks the app.
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:5000`;
const TOKEN_KEY = "scholarmatch_token";

// Kept in localStorage so the profile stays on this device between visits:
// a device account (no email/password) has no other way back in. Older
// builds used sessionStorage, so read that too and move it over once.
function store(fn) {
  try {
    return fn();
  } catch {
    return null; // storage blocked (private mode etc.): works for this visit only
  }
}

let memoryToken = null;

export function getToken() {
  return (
    store(() => {
      const legacy = window.sessionStorage.getItem(TOKEN_KEY);
      if (legacy) {
        window.localStorage.setItem(TOKEN_KEY, legacy);
        window.sessionStorage.removeItem(TOKEN_KEY);
      }
      return window.localStorage.getItem(TOKEN_KEY);
    }) || memoryToken
  );
}

export function setToken(token) {
  if (!token) return;
  memoryToken = token;
  store(() => window.localStorage.setItem(TOKEN_KEY, token));
}

export function clearToken() {
  memoryToken = null;
  store(() => {
    window.localStorage.removeItem(TOKEN_KEY);
    window.sessionStorage.removeItem(TOKEN_KEY);
  });
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
    window.location.href = "/";
    throw new Error("Your session ended. Please start again.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

// --- Auth ---
// One tap, no email or password: makes a profile tied to this device.
export const startOnDevice = (consents) =>
  request("/api/auth/device", { method: "POST", body: consents, auth: false });

export const signup = (email, password, consents) =>
  request("/api/auth/signup", {
    method: "POST",
    body: { email, password, ...consents },
    auth: false,
  });

export const login = (email, password) =>
  request("/api/auth/login", { method: "POST", body: { email, password }, auth: false });

export const getMe = () => request("/api/auth/me");

// Moving a profile to another device: a one-time code made on the old one,
// typed (or scanned) on the new one.
export const makeLinkCode = () => request("/api/auth/link-code", { method: "POST" });
export const redeemLinkCode = (code) =>
  request("/api/auth/link-code/redeem", { method: "POST", body: { code }, auth: false });

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
// Email accounts confirm with their password; device accounts with confirm: true.
export const deleteAccount = (password) =>
  request("/api/account", {
    method: "DELETE",
    body: password ? { password } : { confirm: true },
  });

// --- Stats ---
export const getStats = () => request("/api/stats");

// --- Public (signed-out homepage) ---
export const getPublicPreview = () => request("/api/public/preview", { auth: false });
