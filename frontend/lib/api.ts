import axios from "axios";
import { clearAuth, getAuthToken, getTenantId } from "./auth";
import { appPath } from "@/lib/paths";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "/proxy/8000",
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
    if (error?.response?.status === 401 && typeof window !== "undefined") {
      clearAuth();
      window.location.assign(appPath("/login"));

    }
    return Promise.reject(error);
  },
);
