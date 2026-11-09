// src/main.jsx
// The actual bootstrap of the React app: mounts <App /> into the #root div
// declared in index.html, and pulls in the global stylesheet.

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
// Self-hosted display font (instead of Google Fonts) so no visitor data
// goes to a third party just to render a headline.
import "@fontsource/libre-franklin/600.css";
import "@fontsource/libre-franklin/700.css";
import "./index.css";
import { setupPwa } from "./pwa.js";

setupPwa();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
