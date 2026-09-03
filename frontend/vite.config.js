// vite.config.js
// Vite is the dev server / bundler for the React app. `host: true` lets
// the dev server be reached from outside its container (needed for the
// docker-compose setup) and from a phone on the same Wi-Fi network when
// testing the mobile-first design on a real device.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
});
