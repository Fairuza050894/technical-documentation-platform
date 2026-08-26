export interface AuthSession {
  subject_id: string;
  display_name: string;
  email: string;
  provider: string;
  assurance: string;
  role: string;
}

export interface AuthState {
  status: "loading" | "authenticated" | "unauthenticated";
  session: AuthSession | null;
  token: string | null;
}

export interface CsrfTokenResponse {
  success: boolean;
  data: {
    csrf_token: string;
  };
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}