import { useEffect, useState } from "react";
import { getTenantId, setTenantId } from "./auth";

export function useTenant() {
  const [tenantId, setTenantIdState] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    setTenantIdState(getTenantId() ?? "");
  }, []);

  const updateTenant = (nextTenantId: string) => {
    setTenantId(nextTenantId);
    setTenantIdState(nextTenantId);
  };

  return {
    tenantId,
    updateTenant,
  };
}
