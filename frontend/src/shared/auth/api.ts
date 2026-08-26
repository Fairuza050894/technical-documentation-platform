import { apiUrl } from "../api/config";
import type { AuthSession, CsrfTokenResponse, LogoutResponse } from "./types";

const TOKEN_KEY = "tdp.access_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function storeToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Storage unavailable
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage unavailable
  }
}

export async function fetchSession(token?: string): Promise<AuthSession> {
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(apiUrl("/identity/me"), {
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Session fetch failed: ${response.status}`);
  }

  return (await response.json()) as AuthSession;
}

export async function fetchCsrfToken(): Promise<string> {
  const response = await fetch(apiUrl("/csrf-token"), {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch CSRF token");
  }

  const data = (await response.json()) as CsrfTokenResponse;
  return data.data.csrf_token;
}

export async function logout(token?: string): Promise<LogoutResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(apiUrl("/auth/logout"), {
    method: "POST",
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Logout failed");
  }

  return (await response.json()) as LogoutResponse;
}