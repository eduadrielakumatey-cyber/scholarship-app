// src/components/DeviceLinkPanel.jsx
//
// "Use on another device": shows a one-time code and a QR code that opens
// this profile on a phone, laptop, etc. A device profile has no email or
// password, so this is the only way to carry it over. The code lives in
// the QR link's #fragment, which browsers never send to a server.

import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Smartphone } from "lucide-react";
import * as api from "../api/client.js";

function formatLeft(seconds) {
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export default function DeviceLinkPanel() {
  const [code, setCode] = useState(null);
  const [qr, setQr] = useState(null);
  const [left, setLeft] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!code) return undefined;
    const timer = setInterval(() => setLeft((n) => Math.max(0, n - 1)), 1000);
    return () => clearInterval(timer);
  }, [code]);

  const expired = code && left === 0;

  async function makeCode() {
    setError(null);
    setBusy(true);
    try {
      const data = await api.makeLinkCode();
      const url = `${window.location.origin}/link#${data.code}`;
      setCode(data.code);
      setLeft(data.expires_in_seconds);
      setQr(await QRCode.toDataURL(url, { margin: 1, width: 360 }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="device-link">
      <h3 className="device-link__title">
        <Smartphone size={18} strokeWidth={2.4} aria-hidden="true" /> Use on another device
      </h3>

      {!code || expired ? (
        <>
          <p className="field-help">
            {expired
              ? "That code expired. Make a new one when you're ready."
              : "Get a one-time code to open this same profile, with your saved scholarships, on your phone or another computer."}
          </p>
          <button type="button" className="secondary-button" onClick={makeCode} disabled={busy}>
            {busy ? "Making a code..." : "Get a code"}
          </button>
        </>
      ) : (
        <div className="device-link__code-box">
          {qr && <img className="device-link__qr" src={qr} alt="QR code that opens this profile" />}
          <div>
            <p className="device-link__code" aria-label={`Code ${code.split("").join(" ")}`}>
              {code}
            </p>
            <p className="field-help">
              Scan the QR code with your other device's camera, or go to{" "}
              <strong>{window.location.host}/link</strong> there and type the code.
            </p>
            <p className="field-help">
              Works once. Expires in {formatLeft(left)}. Don't share it: anyone with it can open
              your profile.
            </p>
          </div>
        </div>
      )}

      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
