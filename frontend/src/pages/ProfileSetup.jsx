// src/pages/ProfileSetup.jsx
//
// Collects the exact inputs the matching engine needs: GPA, grade level,
// state, demographics, interests, major. Chip-style multi-select for
// demographics/interests (tap to toggle) rather than a checkbox list --
// faster to scan and tap on a phone screen.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { GRADE_LEVELS } from "../constants/gradeLevels.js";

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME",
  "MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA",
  "RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
];

const DEMOGRAPHIC_OPTIONS = [
  "first-generation", "female", "male", "veteran", "rural", "lgbtq+",
  "hispanic", "black", "asian", "native-american", "disability",
];

const INTEREST_OPTIONS = [
  "stem", "robotics", "coding", "art", "music", "writing",
  "community service", "leadership", "sports", "business", "healthcare",
];

function ChipSelect({ options, selected, onToggle }) {
  return (
    <div className="chip-row">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className="chip"
          aria-pressed={selected.includes(option)}
          onClick={() => onToggle(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

export default function ProfileSetup() {
  const { user, updateProfile } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    gpa: "",
    grade_level: "",
    state: "",
    major: "",
    demographics: [],
    interests: [],
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm({
      full_name: user.full_name || "",
      gpa: user.gpa ?? "",
      grade_level: user.grade_level || "",
      state: user.state || "",
      major: user.major || "",
      demographics: user.demographics || [],
      interests: user.interests || [],
    });
  }, [user]);

  function toggleChip(field, value) {
    setForm((prev) => {
      const list = prev[field];
      const next = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
      return { ...prev, [field]: next };
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await updateProfile({
        ...form,
        gpa: form.gpa === "" ? null : Number(form.gpa),
      });
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="screen">
      <h1 className="page-title">Your profile</h1>
      <p className="page-subtitle">
        This is exactly what the matching engine uses to estimate your odds -- the more accurate,
        the better your matches.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="field-group">
          <label htmlFor="full_name">Full name</label>
          <input
            id="full_name"
            type="text"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
        </div>

        <div className="field-group">
          <label htmlFor="gpa">GPA (0.0–5.0 scale)</label>
          <input
            id="gpa"
            type="number"
            step="0.01"
            min="0"
            max="5"
            placeholder="e.g. 3.75"
            value={form.gpa}
            onChange={(e) => setForm({ ...form, gpa: e.target.value })}
            required
          />
        </div>

        <div className="field-group">
          <label htmlFor="grade_level">Grade level</label>
          <select
            id="grade_level"
            value={form.grade_level}
            onChange={(e) => setForm({ ...form, grade_level: e.target.value })}
            required
          >
            <option value="" disabled>
              Select grade
            </option>
            {GRADE_LEVELS.map((g) => (
              <option key={g.value} value={g.value}>
                {g.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field-group">
          <label htmlFor="state">State</label>
          <select
            id="state"
            value={form.state}
            onChange={(e) => setForm({ ...form, state: e.target.value })}
            required
          >
            <option value="" disabled>
              Select state
            </option>
            {US_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="field-group">
          <label htmlFor="major">Intended major</label>
          <input
            id="major"
            type="text"
            placeholder="e.g. computer science"
            value={form.major}
            onChange={(e) => setForm({ ...form, major: e.target.value })}
            required
          />
        </div>

        <div className="field-group">
          <label>Demographics (optional, helps surface targeted scholarships)</label>
          <ChipSelect
            options={DEMOGRAPHIC_OPTIONS}
            selected={form.demographics}
            onToggle={(v) => toggleChip("demographics", v)}
          />
        </div>

        <div className="field-group">
          <label>Interests</label>
          <ChipSelect
            options={INTEREST_OPTIONS}
            selected={form.interests}
            onToggle={(v) => toggleChip("interests", v)}
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save and find matches"}
        </button>
      </form>
    </div>
  );
}
