// src/components/InstallPrompt.jsx
//
// One-time "Add ScholarMatch to your home screen" banner for phones.
// Android/Chrome: a real Install button (the browser's own prompt).
// iPhone/iPad: Safari has no install button for websites, so it explains
// the two taps (Share, then Add to Home Screen).
//
// Shown only to someone with a profile, once the storage notice is out of
// the way, and never inside the installed app itself.

import { useEffect, useState } from "react";
import { Share } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { canPromptInstall, isIOS, isStandalone, onInstallChange, promptInstall } from "../pwa.js";

const DISMISS_KEY = "scholarmatch_install_dismissed";
const STORAGE_NOTICE_KEY = "scholarmatch_storage_notice_dismissed";

function read(key) {
  try {
    return window.localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

export default function InstallPrompt() {
  const { user } = useAuth();
  const [dismissed, setDismissed] = useState(() => read(DISMISS_KEY));
  const [, rerender] = useState(0);

  useEffect(() => onInstallChange(() => rerender((n) => n + 1)), []);

  const ios = isIOS();
  const android = canPromptInstall();
  if (!user || dismissed || isStandalone() || !read(STORAGE_NOTICE_KEY)) return null;
  if (!ios && !android) return null;

  function dismiss() {
    try {
      window.localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // Storage blocked: hide it for this visit.
    }
    setDismissed(true);
  }

  async function install() {
    await promptInstall();
    dismiss();
  }

  return (
    <div className="storage-notice install-prompt" role="region" aria-label="Install the app">
      <img className="install-prompt__icon" src="/icons/icon-192.png" alt="" width="40" height="40" />
      {ios && !android ? (
        <p>
          <strong>Get the app:</strong> tap <Share size={14} aria-label="Share" className="install-prompt__share" />{" "}
          then <strong>Add to Home Screen</strong>.
        </p>
      ) : (
        <p>
          <strong>Get the app:</strong> add ScholarMatch to your home screen. It's free and opens
          full screen.
        </p>
      )}
      {android && (
        <button type="button" className="storage-notice__button" onClick={install}>
          Install
        </button>
      )}
      <button type="button" className="install-prompt__close" onClick={dismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
