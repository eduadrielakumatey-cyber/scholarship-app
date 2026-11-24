// infra/keepwarm-worker.js
//
// Copy of the Cloudflare Worker "scholarmatch-keepwarm" (Cloudflare account of
// eduadrielakumatey, Workers & Pages), deployed from the dashboard on
// 2026-11-24 with a cron trigger of "*/5 * * * *".
//
// Render's free backend sleeps after 15 idle minutes and takes ~30-60s to
// wake, which made the app fail with "Failed to fetch". GitHub's scheduled
// keep-warm workflow (.github/workflows/keep-warm.yml) only ran every few
// hours, so this pings every 5 minutes instead. One always-on free service
// uses ~720-744 of Render's 750 free instance-hours a month.
//
// To change it: edit in the Cloudflare dashboard (Edit code -> Deploy), then
// update this copy. Cron trigger changes need Settings -> Trigger events ->
// Add, then the "Save" button in the "Unsaved changes" bar.

// Pings the ScholarMatch backend every 5 minutes (cron trigger) so Render's free server never falls asleep.
// Retries while the server is waking (429/5xx/network error) for up to ~2 minutes.
const HEALTH = "https://scholarship-app-cyrs.onrender.com/api/health";
const HEADERS = { "User-Agent": "ScholarMatch-keepwarm/1.0 (+https://scholarmatch.app)" };
async function ping() {
  for (let attempt = 1; attempt <= 8; attempt++) {
    try {
      const r = await fetch(HEALTH, { headers: HEADERS });
      console.log("ping", attempt, r.status);
      if (r.ok) return r.status;
    } catch (e) {
      console.log("ping", attempt, "error", String(e));
    }
    await new Promise((res) => setTimeout(res, 15000));
  }
  return 0;
}
export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(ping());
  },
  async fetch() {
    return new Response("backend " + (await ping()));
  },
};
