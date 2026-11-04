// src/components/LegalFooter.jsx
//
// Policy links + who runs the app. Shown on the public screens and at the
// bottom of Profile, so the operator's identity and contact details are
// always one tap away (required by most consumer-protection rules).

import { Link } from "react-router-dom";
import { SITE } from "../legal/siteInfo.js";

export default function LegalFooter() {
  return (
    <footer className="legal-footer">
      <nav className="legal-footer__links" aria-label="Legal">
        <Link to="/terms">Terms</Link>
        <Link to="/privacy">Privacy</Link>
        <Link to="/cookies">Cookies</Link>
        <Link to="/licenses">Licenses</Link>
      </nav>
      <p className="legal-footer__business">
        {SITE.appName} is operated by {SITE.operatorName}{SITE.mailingAddress && `, ${SITE.mailingAddress}`}.{" "}
        Contact: <a href={`mailto:${SITE.contactEmail}`}>{SITE.contactEmail}</a>
      </p>
      <p className="legal-footer__business">
        Free to use. Not affiliated with any scholarship provider listed.
      </p>
    </footer>
  );
}
