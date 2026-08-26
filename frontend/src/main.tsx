import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import { AuthProvider } from "./shared/auth/AuthContext";
import "./styles/globals.css";

// Determine auth mode from environment
const authMode = (import.meta.env.VITE_AUTH_MODE ?? "local") as "local" | "oidc";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Application root element was not found.");
}

createRoot(rootElement).render(
  <StrictMode>
    <AuthProvider authMode={authMode}>
      <App />
    </AuthProvider>
  </StrictMode>,
);
