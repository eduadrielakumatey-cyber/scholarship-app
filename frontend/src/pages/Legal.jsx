// src/pages/Legal.jsx
//
// The public policy pages: Privacy, Terms (which also covers fees and
// refunds -- the app is free), Cookies and Licenses. All business details
// come from legal/siteInfo.js so there's one place to fill them in.
//
// These are written to match what the app ACTUALLY does today (no cookies,
// no analytics, no email sending, no payments). If any of that changes,
// update the matching section here in the same change. Have a lawyer
// review before launch -- this is a solid starting point, not legal advice.

import { Link, useNavigate } from "react-router-dom";
import { SITE, LEGAL_UPDATED_LABEL } from "../legal/siteInfo.js";
import LegalFooter from "../components/LegalFooter.jsx";

function LegalLayout({ title, children }) {
  const navigate = useNavigate();
  return (
    <div className="screen legal-page">
      <button type="button" className="text-link-button" onClick={() => navigate(-1)}>
        ← Back
      </button>
      <h1 className="page-title">{title}</h1>
      <p className="page-subtitle">Last updated {LEGAL_UPDATED_LABEL}</p>
      <div className="legal-body">{children}</div>
      <LegalFooter />
    </div>
  );
}

const contactLink = <a href={`mailto:${SITE.contactEmail}`}>{SITE.contactEmail}</a>;

export function Privacy() {
  return (
    <LegalLayout title="Privacy Policy">
      <p>
        {SITE.appName} ("we", "us") is operated by {SITE.operatorName}{SITE.mailingAddress && `, ${SITE.mailingAddress}`}.
        This policy explains what we collect, why, and the controls you have. Questions:{" "}
        {contactLink}.
      </p>

      <h2>What we collect</h2>
      <ul>
        <li>
          <strong>Account:</strong> none needed. When you start, we create a profile tied to
          your device: a random key is saved in your browser, with no name, email or password.
          (Older accounts made with an email keep that email and a securely hashed password; we
          never store or see the actual password.)
        </li>
        <li>
          <strong>Matching profile:</strong> GPA, grade level, state, intended major and
          interests. These are required because they are exactly what the matcher uses.
        </li>
        <li>
          <strong>Demographics (optional):</strong> things like first-generation status,
          ethnicity, disability or LGBTQ+ identity. Some of this is sensitive, so we only store
          it if you turn on the separate opt-in on your profile, and turning it off erases it.
        </li>
        <li>
          <strong>Activity:</strong> which scholarships you saved or passed on, and the
          application status you set on saved ones.
        </li>
        <li>
          <strong>Consent records:</strong> when you agreed to these policies and when you opted
          in to demographics.
        </li>
        <li>
          <strong>Technical logs:</strong> our hosting providers automatically log IP addresses
          and request details for security and reliability.
        </li>
      </ul>
      <p>We don't ask for your name, address, phone number, birth date or school.</p>

      <h2>How we use it</h2>
      <p>
        Only to run {SITE.appName}: to match you with scholarships, show your saved list and
        stats, keep your account secure, and fix problems. We do not sell or rent your
        information, we don't share it for advertising, and we don't run ads, analytics or
        tracking tools.
      </p>

      <h2>Who we share it with</h2>
      <p>
        Only service providers that host the app and its database on our behalf (currently
        Vercel for the website and Railway for the server and database), under contracts that
        limit their use of it. We may also disclose information if the law requires it. If{" "}
        {SITE.appName} is ever sold or merged, we'll notify you before your information becomes
        subject to a different policy.
      </p>

      <h2>Emails</h2>
      <p>
        We don't currently send any emails. If we ever send marketing or update emails, you'll
        have to opt in first, and every one will include a one-click unsubscribe link.
      </p>

      <h2>How long we keep it</h2>
      <p>
        Until you delete your profile. Deleting removes your profile and activity from
        our database immediately; copies in routine backups are overwritten within 30 days.
      </p>

      <h2>Your rights and controls</h2>
      <ul>
        <li>
          <strong>See and download your data:</strong> Profile → "Download my data".
        </li>
        <li>
          <strong>Correct it:</strong> edit your profile at any time.
        </li>
        <li>
          <strong>Delete it:</strong> Profile → "Delete my profile". No email or waiting period
          needed.
        </li>
      </ul>
      <p>
        Depending on where you live (for example California under the CCPA/CPRA, or the EU/UK
        under the GDPR) you may have additional rights, such as to object to or restrict
        processing, or to complain to a data-protection authority. We honor these requests for
        everyone. Email {contactLink} and we'll respond within 30 days. We will never treat you
        differently for using these rights.
      </p>
      <p>
        Where the GDPR applies, our legal basis is performing our contract with you (running the
        matching service), your explicit consent (demographics) and our legitimate interest in
        keeping the service secure.
      </p>

      <h2>Children and teens</h2>
      <p>
        {SITE.appName} is not for children under 13, and we don't knowingly collect information
        from them. If you're 13 to 17, please use {SITE.appName} with your parent or guardian's
        permission. If you believe a child under 13 has created an account, email{" "}
        {contactLink} and we'll delete it.
      </p>

      <h2>Security</h2>
      <p>
        Passwords are hashed with bcrypt, connections are encrypted (HTTPS), and access to the
        database is restricted. No system is perfectly secure; if a breach affects your
        information we'll notify you as the law requires.
      </p>

      <h2>Where data is stored</h2>
      <p>Your information is stored and processed in the United States.</p>

      <h2>Changes</h2>
      <p>
        If we materially change this policy we'll update the date above and ask you to review
        it in the app before continuing.
      </p>
    </LegalLayout>
  );
}

export function Terms() {
  return (
    <LegalLayout title="Terms of Service">
      <p>
        These terms are an agreement between you and {SITE.operatorName} ({SITE.operatorType}),
        who operates {SITE.appName}. By creating an account you agree to them and to our{" "}
        <Link to="/privacy">Privacy Policy</Link>.
      </p>

      <h2>Who can use {SITE.appName}</h2>
      <p>
        You must be at least 13 years old. If you're under 18, you need your parent or
        guardian's permission, and they agree to these terms on your behalf.
      </p>

      <h2>Price, fees and refunds</h2>
      <p>
        {SITE.appName} is free. There are no subscriptions, in-app purchases, trial periods or
        hidden fees, and we never ask for payment details. Because nothing is charged, there is
        nothing to refund. If we ever introduce a paid feature, we'll show the full price
        before you buy, it will be optional, and we'll publish a refund policy first.
      </p>

      <h2>Scholarship information</h2>
      <ul>
        <li>
          Listings come from scholarship providers' public pages. We're not affiliated with or
          endorsed by them, and we don't decide who wins.
        </li>
        <li>
          Deadlines, amounts and eligibility can change or be wrong. Always confirm details on
          the provider's official site before applying.
        </li>
        <li>
          Match scores, competitiveness levels and value estimates are rough guides computed
          from your profile and the listing. They are not predictions or guarantees of winning.
        </li>
        <li>
          Legitimate scholarships don't charge you to apply. If a listing asks for payment,
          don't pay, and tell us at {contactLink}.
        </li>
      </ul>

      <h2>Your account</h2>
      <p>
        Your profile lives on the device you started it on, so anyone using that browser can
        see it. Give accurate profile information. You can delete your profile at any time from
        the Profile page. We may suspend profiles that break these terms.
      </p>

      <h2>Acceptable use</h2>
      <p>
        Don't misuse the service: no scraping or bulk downloading, no trying to access other
        people's accounts, no interfering with the app's operation, and nothing illegal.
      </p>

      <h2>Our content</h2>
      <p>
        The {SITE.appName} app, name and design belong to {SITE.operatorName}. Scholarship names
        and logos belong to their owners. Third-party licenses are listed on the{" "}
        <Link to="/licenses">Licenses</Link> page.
      </p>

      <h2>Disclaimers and liability</h2>
      <p>
        {SITE.appName} is provided "as is" without warranties of any kind. To the extent the law
        allows, we're not liable for indirect or consequential losses, including missed
        deadlines or unsuccessful applications, and our total liability is limited to $50.
        Nothing here limits rights you have under consumer-protection law that can't be waived.
      </p>

      <h2>Changes and governing law</h2>
      <p>
        We'll notify you in the app before material changes take effect. These terms are
        governed by the laws of the State of {SITE.governingState}, USA.
      </p>

      <h2>Contact</h2>
      <p>
        {SITE.operatorName}{SITE.mailingAddress && `, ${SITE.mailingAddress}`}. {contactLink}
      </p>
    </LegalLayout>
  );
}

export function Cookies() {
  return (
    <LegalLayout title="Cookie Policy">
      <p>
        Short version: {SITE.appName} doesn't use cookies, analytics, advertising pixels or any
        other tracking.
      </p>

      <h2>What we store in your browser</h2>
      <table className="legal-table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Type</th>
            <th scope="col">Purpose</th>
            <th scope="col">Lasts</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>scholarmatch_token</td>
            <td>Local storage</td>
            <td>Keeps your profile on this device, so you don't need to sign in</td>
            <td>Until you delete your profile or clear site data (the key expires after a year)</td>
          </tr>
          <tr>
            <td>scholarmatch_storage_notice_dismissed</td>
            <td>Local storage</td>
            <td>Remembers you closed the storage notice</td>
            <td>Until you clear site data</td>
          </tr>
          <tr>
            <td>scholarmatch_tour_done</td>
            <td>Local storage</td>
            <td>Remembers you finished or skipped Scout's walkthrough</td>
            <td>Until you clear site data</td>
          </tr>
        </tbody>
      </table>
      <p>
        These are all needed for features you use, so they don't require consent and
        there's nothing to switch off. None of them track you. You can clear them at any time in your browser settings.
      </p>

      <h2>Third parties</h2>
      <p>
        Fonts are served from our own site, not from Google or another font service, and we
        load no third-party scripts. Our hosting providers keep standard server logs (see the{" "}
        <Link to="/privacy">Privacy Policy</Link>).
      </p>

      <h2>If this changes</h2>
      <p>
        If we ever add optional cookies such as analytics, they will stay off until you agree,
        and we'll update this page first.
      </p>
    </LegalLayout>
  );
}

const LICENSES = [
  ["Libre Franklin typeface", "SIL Open Font License 1.1", "Impallari Type"],
  ["React, React DOM", "MIT License", "Meta Platforms, Inc."],
  ["React Router", "MIT License", "Remix Software Inc."],
  ["Fontsource", "MIT License", "Fontsource contributors"],
  ["Lucide icons", "ISC License", "Lucide contributors"],
  ["Flask, Flask-SQLAlchemy, Flask-Migrate", "BSD-3-Clause License", "Pallets and contributors"],
  ["Flask-JWT-Extended, Flask-CORS", "MIT License", "Their respective authors"],
  ["bcrypt", "Apache License 2.0", "The Python Cryptographic Authority"],
];

export function Licenses() {
  return (
    <LegalLayout title="Licenses & credits">
      <p>
        {SITE.appName} uses no stock photos or licensed images. Interface icons come from the
        open-source Lucide set, and Scout, our guide character, is original artwork.
      </p>

      <h2>Open-source software and fonts</h2>
      <table className="legal-table">
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">License</th>
            <th scope="col">Copyright</th>
          </tr>
        </thead>
        <tbody>
          {LICENSES.map(([name, license, holder]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>{license}</td>
              <td>{holder}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>Full license texts are included with each package's source code.</p>

      <h2>Scholarship listings</h2>
      <p>
        Scholarship facts (name, amount, deadline, eligibility) are summarized from each
        provider's public page, and every listing links back to its official source. Names and
        trademarks belong to their owners. If you own a listing and want it corrected or
        removed, email {contactLink}.
      </p>
    </LegalLayout>
  );
}
