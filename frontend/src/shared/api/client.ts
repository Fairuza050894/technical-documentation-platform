interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
}

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`http://127.0.0.1:8000/api${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload = {};
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      // Keep a stable fallback for non-JSON transport failures.
    }
    throw new ApiClientError(
      payload.error?.message ?? "The request could not be completed.",
      payload.error?.code ?? "REQUEST_FAILED",
      response.status,
    );
  }

  return (await response.json()) as T;
}
