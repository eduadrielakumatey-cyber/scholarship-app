// src/constants/gradeLevels.js
//
// "12" = high school senior; the rest are college class years. Most users
// of this app are college students, not younger high schoolers, so 9th-11th
// grade were dropped as selectable options. Shared between the profile form
// (which needs the full {value, label} list) and anywhere a scholarship's
// grade_levels need a human-readable label (which just needs the lookup).

export const GRADE_LEVELS = [
  { value: "12", label: "High School Senior" },
  { value: "college_1", label: "College Freshman" },
  { value: "college_2", label: "College Sophomore" },
  { value: "college_3", label: "College Junior" },
  { value: "college_4", label: "College Senior" },
  { value: "college_5plus", label: "5th Year+ / Graduate Student" },
];

const LABEL_BY_VALUE = Object.fromEntries(GRADE_LEVELS.map((g) => [g.value, g.label]));

export function gradeLevelLabel(value) {
  return LABEL_BY_VALUE[value] || value;
}
