// Typed fetch helpers for communicating with the backend API.
const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not configured");
}

type RequestOptions = Omit<RequestInit, "body" | "method">;

async function request<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  get<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return request<T>(path, { ...options, method: "GET" });
  },

  post<TResponse, TBody>(
    path: string,
    body: TBody,
    options: RequestOptions = {},
  ): Promise<TResponse> {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");

    return request<TResponse>(path, {
      ...options,
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
  },
};

