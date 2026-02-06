import { getAuthToken, getTenantId } from "./auth";
import { appPath } from "@/lib/paths";

export function requireAuthOrRedirect() {
  if (typeof window === "undefined") return;

  const token = getAuthToken();
  const tenantId = getTenantId();

  if (!token || !tenantId) {
    window.location.assign(appPath("/login"));

  }
}
