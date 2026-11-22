// src/constants/counties.js
//
// Maryland's 23 counties plus Baltimore City. Keep in sync with MD_COUNTIES
// in backend/app/utils/validators.py: the backend rejects any other name.

export const MD_COUNTIES = [
  "Allegany", "Anne Arundel", "Baltimore City", "Baltimore County", "Calvert",
  "Caroline", "Carroll", "Cecil", "Charles", "Dorchester", "Frederick", "Garrett",
  "Harford", "Howard", "Kent", "Montgomery", "Prince George's", "Queen Anne's",
  "St. Mary's", "Somerset", "Talbot", "Washington", "Wicomico", "Worcester",
];

// "Carroll" -> "Carroll County"; "Baltimore City" stays as is.
export function countyLabel(name) {
  return name.endsWith("City") || name.endsWith("County") ? name : `${name} County`;
}
