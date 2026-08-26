import { useState } from "react";

import { Icon } from "../ui/Icon";

interface LoginPageProps {
  authMode: "local" | "oidc";
  onLogin: (token?: string) => Promise<void>;
}

export function LoginPage({ authMode, onLogin }: LoginPageProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLocalLogin = async (): Promise<void> => {
    setIsLoading(true);
    setError("");
    try {
      await onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOidcLogin = (): void => {
    // Redirect to OIDC provider
    // In a real implementation, this would construct the OIDC authorize URL
    const redirectUri = `${window.location.origin}/auth/callback`;
    const clientId = import.meta.env.VITE_OIDC_CLIENT_ID ?? "";
    const issuer = import.meta.env.VITE_OIDC_ISSUER ?? "";

    if (!issuer || !clientId) {
      setError("OIDC configuration is missing.");
      return;
    }

    const params = new URLSearchParams({
      response_type: "code",
      client_id: clientId,
      redirect_uri: redirectUri,
      scope: "openid profile email",
      state: crypto.randomUUID(),
    });

    window.location.href = `${issuer}/authorize?${params.toString()}`;
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <span className="login-card__icon" aria-hidden="true">
            <Icon name="documents" size={28} />
          </span>
          <h1>Technical Documentation Platform</h1>
          <p>Sign in to continue</p>
        </div>

        {error && (
          <div className="login-card__error" role="alert">
            {error}
          </div>
        )}

        <div className="login-card__actions">
          {authMode === "local" && (
            <button
              type="button"
              className="login-card__button login-card__button--primary"
              onClick={handleLocalLogin}
              disabled={isLoading}
            >
              {isLoading ? "Signing in…" : "Continue as Developer"}
            </button>
          )}

          {authMode === "oidc" && (
            <button
              type="button"
              className="login-card__button login-card__button--primary"
              onClick={handleOidcLogin}
              disabled={isLoading}
            >
              <Icon name="server" size={16} />
              {isLoading ? "Redirecting…" : "Sign in with SSO"}
            </button>
          )}
        </div>

        <div className="login-card__footer">
          <small>
            {authMode === "local"
              ? "Development mode — no real authentication"
              : "Protected by your organization's identity provider"}
          </small>
        </div>
      </div>
    </div>
  );
}