import { getAuthToken, getTenantId } from "./auth";

export function requireAuthOrRedirect() {
  if (typeof window === "undefined") return;

  const token = getAuthToken();
  const tenantId = getTenantId();

  if (!token || !tenantId) {
    window.location.assign("/login");
  }
}
