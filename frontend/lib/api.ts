import axios from "axios";
import { clearAuth, getAuthToken, getTenantId } from "./auth";
import { appPath } from "@/lib/paths";

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
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
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
    const status = error?.response?.status;
    const responseData = error?.response?.data;

    if (status === 401 && typeof window !== "undefined") {
      clearAuth();
      window.location.assign(appPath("/login"));
    } else if (status === 403) {
      publishApiError({
        status: 403,
        message: "You are not authorized to perform this action.",
        payload: responseData,
      });
    } else if (status === 409) {
      publishApiError({
        status: 409,
        message: "A conflict was detected. Review the details and try again.",
        payload: responseData,
      });
    }
    return Promise.reject(error);
  },
);
