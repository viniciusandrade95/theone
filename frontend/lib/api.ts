import axios from "axios";
import { clearAuth, getAuthToken, getTenantId } from "./auth";
import { appPath } from "@/lib/paths";
import { parseApiError } from "@/lib/api-errors";

export const API_ERROR_EVENT = "app:api-error";

type ApiErrorDetail = {
  status: number;
  message: string;
  payload?: unknown;
};

function publishApiError(detail: ApiErrorDetail) {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new CustomEvent<ApiErrorDetail>(API_ERROR_EVENT, { detail }));
}

export const api = axios.create({
  // Prefer same-origin requests in production, relying on Next.js route handlers to proxy to the API.
  // This avoids CORS complexity and prevents mis-baked NEXT_PUBLIC_* env vars from breaking auth.
  baseURL: "",
});

api.interceptors.request.use((config) => {
  if (typeof window === "undefined") return config;

  const token = getAuthToken();
  const tenant = getTenantId();

  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenant) config.headers["X-Tenant-ID"] = tenant;

  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const parsed = parseApiError(error, "Request failed.");
    const status = parsed.status;
    const responseData = parsed.payload;

    if (status === 401 && typeof window !== "undefined") {
      clearAuth();
      window.location.assign(appPath("/login"));
    } else if (status === 403) {
      publishApiError({
        status: 403,
        message: parsed.message,
        payload: responseData,
      });
    } else if (status === 409) {
      publishApiError({
        status: 409,
        message: parsed.message,
        payload: responseData,
      });
    }
    return Promise.reject(error);
  },
);
