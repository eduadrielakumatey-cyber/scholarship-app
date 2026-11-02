// src/components/StorageNotice.jsx
//
// One-time notice about browser storage. ScholarMatch sets no cookies and
// runs no analytics or ad trackers -- the only thing stored is the sign-in
// token (sessionStorage) and this notice's own dismissal flag -- both
// strictly necessary, so there's nothing optional to accept or reject.
// An "Accept / Reject" banner here would imply tracking that doesn't
// exist; if you ever add analytics or marketing pixels, this must become
// a real opt-in banner that blocks them until the user agrees.

import { useState } from "react";
import { Link } from "react-router-dom";

const DISMISS_KEY = "scholarmatch_storage_notice_dismissed";

function readDismissed() {
  try {
    return window.localStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

export default function StorageNotice() {
  const [dismissed, setDismissed] = useState(readDismissed);
  if (dismissed) return null;

  function dismiss() {
    try {
      window.localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // Private mode / blocked storage: just hide it for this visit.
    }
    setDismissed(true);
  }

  return (
    <div className="storage-notice" role="region" aria-label="Cookie and storage notice">
      <p>
        We don't use cookies, ads or tracking. We only store what's needed to keep you signed
        in. <Link to="/cookies">Cookie policy</Link>
      </p>
      <button type="button" className="storage-notice__button" onClick={dismiss}>
        Got it
      </button>
    </div>
  );
}
