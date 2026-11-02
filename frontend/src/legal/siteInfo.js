// src/legal/siteInfo.js
//
// The business details every legal page, the footer and the signup form
// pull from. One place to fill in before launch -- anything still wrapped
// in [brackets] is a placeholder that MUST be replaced with your real
// details (a missing operator name/contact is itself a compliance gap).

export const SITE = {
  appName: "ScholarMatch",
  operatorName: "[Your legal name or company name]",
  operatorType: "[sole proprietor / LLC]",
  mailingAddress: "[Street address, City, State ZIP, USA]",
  contactEmail: "[privacy@yourdomain.com]",
  governingState: "[State]",
  websiteUrl: "[https://yourdomain.com]",
};

// Shown as "Last updated" on each policy. Keep in sync with TERMS_VERSION
// in backend/config.py -- bump both when the Terms or Privacy Policy
// materially change.
export const LEGAL_VERSION = "2026-11-01";
export const LEGAL_UPDATED_LABEL = "November 1, 2026";
