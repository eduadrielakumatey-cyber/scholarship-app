// src/pages/ProfileSetup.jsx
//
// Collects the exact inputs the matching engine needs: GPA, grade level,
// state, demographics, interests, major. Chip-style multi-select for
// demographics/interests (tap to toggle) rather than a checkbox list --
// faster to scan and tap on a phone screen.
//
// Doubles as the start screen (/start): with nobody signed in it shows the
// two required consent boxes, and submitting creates a profile tied to this
// device -- no email, no password -- then saves the answers in one go.

import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { GRADE_LEVELS } from "../constants/gradeLevels.js";
import InterestSelector from "../components/InterestSelector.jsx";
import AccountSettings from "../components/AccountSettings.jsx";
import LegalFooter from "../components/LegalFooter.jsx";
import Guide from "../components/guide/Guide.jsx";
import { getSchools } from "../api/client.js";

const DEMOGRAPHIC_OPTIONS = [
  "first-generation", "female", "male", "veteran", "rural", "lgbtq+",
  "hispanic", "black", "asian", "native-american", "disability",
];

const INTEREST_OPTIONS = [
  "stem", "robotics", "coding", "art", "music", "writing",
  "community service", "leadership", "sports", "business", "healthcare",
];

// Scout's tip for whichever part of the form the student is on.
function guideReaction(field, form, { saving, error, isNewProfile }) {
  if (saving) return { mood: "excited", message: "Crunching your matches..." };
  if (error) return { mood: "sad", message: `Almost! ${error}` };
  const gpa = Number(form.gpa);
  switch (field) {
    case "gpa":
      if (form.gpa !== "" && gpa >= 3.5) return { mood: "wow", message: "Ooh, that GPA opens a lot of doors!" };
      if (form.gpa !== "" && gpa > 0 && gpa < 2.5) {
        return { mood: "happy", message: "Plenty of scholarships don't look at GPA at all. I'll find those." };
      }
      return { mood: "curious", message: "Use the scale your school uses (up to 5.0). Weighted is fine." };
    case "grade_level":
      return { mood: "thinking", message: "Some scholarships are only for high school seniors, others only for college students." };
    case "state":
      return { mood: "happy", message: "Local money is the best money: state scholarships usually get fewer applicants." };
    case "schools":
      return {
        mood: "thinking",
        message: "Most local awards are for one college's own students. Pick yours so I can hide the rest.",
      };
    case "major":
      return { mood: "curious", message: "Not sure yet? Put your best guess. You can change it anytime." };
    case "demographics":
      return {
        mood: "thinking",
        message: "Totally optional. Some awards are set aside for specific groups, and this helps me find them.",
      };
    case "interests":
      if (form.interests.length >= 3) return { mood: "excited", message: "Love it! That's plenty for me to match on." };
      if (form.interests.length > 0) return { mood: "happy", message: "Good start! Three or more gives me more to work with." };
      return { mood: "curious", message: "Pick a few things you love, or add your own." };
    default:
      return isNewProfile
        ? { mood: "happy", message: "Let's build your profile! I only ask for what helps me match you." }
        : { mood: "idle", message: "Update anything here and I'll refresh your matches." };
  }
}

// Colleges the student attends or might attend. null = "not sure yet"
// (show every college's awards); a list (even empty) hides awards that
// only other colleges' students can get; undefined = not answered yet,
// which the required radios block on submit.
function SchoolPicker({ value, onChange }) {
  const [options, setOptions] = useState(null);
  useEffect(() => {
    getSchools().then(setOptions).catch(() => setOptions({ schools: [], any_school_count: 0 }));
  }, []);
  const picking = Array.isArray(value);
  const toggle = (name) =>
    onChange(value.includes(name) ? value.filter((s) => s !== name) : [...value, name]);

  return (
    <fieldset className="field-group field-group--fieldset school-picker" data-guide="schools" id="college">
      <legend>Pick your college</legend>
      <p className="school-picker__why">
        Most scholarships here are only for students at one college. Pick the colleges you go to
        or are thinking about, so you only see scholarships you can actually get.
      </p>
      <label className="consent-check">
        <input type="radio" name="school-mode" required checked={picking} onChange={() => onChange(value ?? [])} />
        <span>
          <strong>Show scholarships for the colleges I pick</strong>
        </span>
      </label>
      {picking && (
        <div className="school-list">
          {options === null && <p className="field-help">Loading colleges...</p>}
          {options?.schools.map((s) => (
            <label key={s.name} className="consent-check school-option">
              <input type="checkbox" checked={value.includes(s.name)} onChange={() => toggle(s.name)} />
              <span>
                {s.name} <span className="school-option__count">{s.count}</span>
              </span>
            </label>
          ))}
          {options && (
            <p className="field-help">
              {value.length === 0
                ? `None checked: you'll only see the ${options.any_school_count} scholarships open to students at any college.`
                : `Scholarships open to students at any college (${options.any_school_count}) always show.`}
            </p>
          )}
        </div>
      )}
      <label className="consent-check">
        <input type="radio" name="school-mode" required checked={value === null} onChange={() => onChange(null)} />
        <span>I&apos;m not sure yet: show scholarships from every college</span>
      </label>
    </fieldset>
  );
}

function ChipSelect({ options, selected, onToggle, disabled = false }) {
  return (
    <div className="chip-row">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className="chip"
          aria-pressed={selected.includes(option)}
          disabled={disabled}
          onClick={() => onToggle(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

export default function ProfileSetup() {
  const { user, updateProfile, startOnDevice } = useAuth();
  const isStarting = !user;
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const navigate = useNavigate();

  const [form, setForm] = useState({
    gpa: "",
    grade_level: "",
    state: "MD",
    major: "",
    demographics: [],
    demographics_consent: false,
    interests: [],
    schools: undefined,
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [activeField, setActiveField] = useState(null);

  useEffect(() => {
    // A brand-new device profile has nothing saved yet: keep what the
    // student just typed instead of resetting the form to blanks.
    if (!user || (!user.profile_complete && user.gpa == null && !user.state)) return;
    setForm({
      gpa: user.gpa ?? "",
      grade_level: user.grade_level || "",
      state: "MD", // Maryland-only launch
      major: user.major || "",
      demographics: user.demographics || [],
      demographics_consent: Boolean(user.demographics_consent),
      interests: user.interests || [],
      schools: user.schools ?? null,
    });
  }, [user]);

  // "Pick my college" on Discover links to /profile#college.
  useEffect(() => {
    if (window.location.hash !== "#college") return;
    const t = setTimeout(() => document.getElementById("college")?.scrollIntoView({ behavior: "smooth", block: "center" }), 300);
    return () => clearTimeout(t);
  }, []);

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
      if (isStarting) {
        await startOnDevice({ age_confirmed: ageConfirmed, accepted_terms: acceptedTerms });
      }
      await updateProfile({
        ...form,
        gpa: form.gpa === "" ? null : Number(form.gpa),
        schools: form.schools ?? null,
        demographics: form.demographics_consent ? form.demographics : [],
      });
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const reaction = guideReaction(activeField, form, {
    saving,
    error,
    isNewProfile: !user?.profile_complete,
  });

  function trackField(e) {
    const field = e.target.closest("[data-guide]")?.dataset.guide || e.target.id;
    if (field) setActiveField(field);
  }

  return (
    <div className="screen">
      <Guide mood={reaction.mood} message={reaction.message} size={64} className="guide-dock profile-guide" />
      <h1 className="page-title">{isStarting ? "Find your matches" : "Your profile"}</h1>
      <p className="page-subtitle">
        {isStarting
          ? "No sign-up. Answer a few questions and start swiping. Your profile stays on this device."
          : "This is exactly what the matching engine uses to estimate your fit: the more accurate, the better your matches."}
      </p>

      <form onSubmit={handleSubmit} onFocusCapture={trackField} onClickCapture={trackField}>
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
          {/* Maryland-only launch: the state is fixed. */}
          <select id="state" value="MD" disabled>
            <option value="MD">Maryland</option>
          </select>
          <p className="field-help">ScholarMatch is just for Maryland students right now.</p>
        </div>

        <SchoolPicker value={form.schools} onChange={(schools) => setForm((prev) => ({ ...prev, schools }))} />

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

        <fieldset className="field-group field-group--fieldset" data-guide="demographics">
          <legend>Demographics (optional)</legend>
          <p className="field-help">
            Some scholarships are only for specific groups. Sharing this is entirely optional,
            is only used for matching, and turning it off erases it.
          </p>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={form.demographics_consent}
              onChange={(e) =>
                setForm({
                  ...form,
                  demographics_consent: e.target.checked,
                  demographics: e.target.checked ? form.demographics : [],
                })
              }
            />
            <span>
              I agree to ScholarMatch using the demographic details I select for matching (see
              the <Link to="/privacy">Privacy Policy</Link>).
            </span>
          </label>
          {form.demographics_consent && (
            <ChipSelect
              options={DEMOGRAPHIC_OPTIONS}
              selected={form.demographics}
              onToggle={(v) => toggleChip("demographics", v)}
            />
          )}
        </fieldset>

        <div className="field-group" data-guide="interests">
          <span className="field-label" id="interests-label">Interests</span>
          <div role="group" aria-labelledby="interests-label">
            <InterestSelector
              options={INTEREST_OPTIONS}
              selected={form.interests}
              onChange={(next) => setForm((prev) => ({ ...prev, interests: next }))}
            />
          </div>
        </div>

        {isStarting && (
          <div className="consent-group">
            <label className="consent-check">
              <input
                type="checkbox"
                required
                checked={ageConfirmed}
                onChange={(e) => setAgeConfirmed(e.target.checked)}
              />
              <span>
                I'm at least 13 years old. If I'm under 18, my parent or guardian has said it's OK.
              </span>
            </label>
            <label className="consent-check">
              <input
                type="checkbox"
                required
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <span>
                I agree to the <Link to="/terms">Terms of Service</Link> and{" "}
                <Link to="/privacy">Privacy Policy</Link>.
              </span>
            </label>
          </div>
        )}

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Saving..." : isStarting ? "Start swiping" : "Save and find matches"}
        </button>
      </form>

      {!isStarting && <AccountSettings />}
      <LegalFooter />
    </div>
  );
}
