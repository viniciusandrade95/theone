import { getAuthToken, getTenantId } from "./auth";
import { appPath } from "@/lib/paths";

export function requireAuthOrRedirect(): boolean {
  if (typeof window === "undefined") return true;

  const token = getAuthToken();
  const tenantId = getTenantId();

  if (!token || !tenantId) {
    window.location.assign(appPath("/login"));
    return false;
  }
  return true;
}
