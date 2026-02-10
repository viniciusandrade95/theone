"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { clearAuth, getTenantId } from "@/lib/auth";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";

type Me = {
  email: string;
};

const pageTitleByPath: Array<{ path: string; title: string }> = [
  { path: "/dashboard/calendar", title: "Calendar" },
  { path: "/dashboard/appointments", title: "Appointments" },
  { path: "/dashboard/customers", title: "Customers" },
  { path: "/dashboard/services", title: "Services" },
  { path: "/dashboard/analytics", title: "Analytics" },
  { path: "/dashboard/settings", title: "Settings" },
];

function resolveTitle(pathname: string) {
  const hit = pageTitleByPath.find((item) => pathname === item.path || pathname.startsWith(`${item.path}/`));
  return hit?.title ?? "Dashboard";
}

export function TopBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const pageTitle = useMemo(() => resolveTitle(pathname), [pathname]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const currentTenantId = getTenantId();
    setTenantId(currentTenantId);
    if (!currentTenantId) {
      return;
    }

    let isMounted = true;
    void api
      .get<Me>("/auth/me")
      .then((response) => {
        if (isMounted) {
          setEmail(response.data.email ?? null);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = () => {
    clearAuth();
    window.location.assign(appPath("/login"));
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-6 py-4 backdrop-blur">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Beauty CRM</p>
          <h2 className="text-xl font-semibold text-slate-900">{pageTitle}</h2>
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-xl border border-slate-200 px-3 py-2 text-left text-sm hover:bg-slate-50"
          >
            <p className="font-semibold text-slate-900">{email ?? "User"}</p>
            <p className="text-xs text-slate-500">Tenant {tenantId ?? "-"}</p>
          </button>

          {menuOpen ? (
            <div className="absolute right-0 mt-2 w-60 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
              <button
                type="button"
                onClick={handleLogout}
                className="w-full rounded-lg px-3 py-2 text-left text-sm font-semibold text-slate-800 hover:bg-slate-100"
              >
                Logout
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
