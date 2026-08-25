// Central typed fetch client with authentication and user-friendly API errors.
import { clearStoredAuth, getAccessToken } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ErrorPayload {
  detail?: string | Array<{ msg?: string }>;
  message?: string;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

function messageFromPayload(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null) return fallback;
  const errorPayload = payload as ErrorPayload;
  if (typeof errorPayload.detail === "string") return errorPayload.detail;
  if (Array.isArray(errorPayload.detail)) {
    const firstMessage = errorPayload.detail[0]?.msg;
    if (firstMessage) return firstMessage;
  }
  return typeof errorPayload.message === "string" ? errorPayload.message : fallback;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });
  } catch {
    throw new ApiError("Unable to reach the server. Please try again.", 0);
  }

  const payload: unknown = response.status === 204
    ? null
    : await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && !path.endsWith("/auth/login")) {
      clearStoredAuth();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    throw new ApiError(
      messageFromPayload(payload, "The request could not be completed."),
      response.status,
    );
  }

  return payload as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

