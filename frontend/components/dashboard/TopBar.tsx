"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { clearAuth, getTenantId } from "@/lib/auth";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";
import { MobileNav } from "@/components/dashboard/MobileNav";
import { IconMenu, IconLogout } from "@/components/ui/icons";

type Me = {
  email: string;
};

type BillingStatus = {
  tier: string;
  active: boolean;
  whatsapp_enabled: boolean;
};

const pageTitleByPath: Array<{ path: string; title: string }> = [
  { path: "/dashboard", title: "Overview" },
  { path: "/dashboard/calendar", title: "Calendar" },
  { path: "/dashboard/appointments", title: "Appointments" },
  { path: "/dashboard/customers", title: "Customers" },
  { path: "/dashboard/services", title: "Services" },
  { path: "/dashboard/analytics", title: "Analytics" },
  { path: "/dashboard/assistant", title: "Assistant" },
  { path: "/dashboard/settings", title: "Settings" },
];

function resolveTitle(pathname: string) {
  const candidates = pageTitleByPath.filter((item) => pathname === item.path || pathname.startsWith(`${item.path}/`));
  if (candidates.length === 0) {
    return "Dashboard";
  }
  candidates.sort((a, b) => b.path.length - a.path.length);
  return candidates[0]?.title ?? "Dashboard";
}

export function TopBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null);
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
    void Promise.all([
      api.get<Me>("/auth/me").catch(() => null),
      api.get<BillingStatus>("/billing/status").catch(() => null),
    ]).then(([meResponse, billingResponse]) => {
      if (!isMounted) return;
      setEmail(meResponse?.data?.email ?? null);
      setBillingStatus(billingResponse?.data ?? null);
    });

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
      <MobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileNavOpen(true)}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white p-2 text-slate-700 transition-colors duration-200 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 lg:hidden"
            aria-label="Open navigation menu"
            aria-haspopup="dialog"
            aria-expanded={mobileNavOpen}
          >
            <IconMenu className="h-5 w-5" />
          </button>

          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Beauty CRM</p>
            <h2 className="text-xl font-semibold text-slate-900">{pageTitle}</h2>
          </div>
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-xl border border-slate-200 px-3 py-2 text-left text-sm transition-colors duration-200 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          >
            <p className="font-semibold text-slate-900">{email ?? "User"}</p>
            <p className="text-xs text-slate-500">
              {billingStatus?.tier ? `${billingStatus.tier.toUpperCase()} plan` : `Tenant ${tenantId ?? "-"}`}
            </p>
          </button>

          {menuOpen ? (
            <div className="absolute right-0 mt-2 w-60 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
              <div className="space-y-1 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                <p className="font-semibold text-slate-900">
                  Plan:{" "}
                  <span className="font-semibold text-slate-900">
                    {billingStatus?.tier ? billingStatus.tier.toUpperCase() : "—"}
                  </span>
                </p>
                <p>WhatsApp: {billingStatus ? (billingStatus.whatsapp_enabled ? "Enabled" : "Disabled") : "—"}</p>
                <p className="text-slate-500">Tenant: {tenantId ?? "—"}</p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm font-semibold text-slate-800 transition-colors duration-200 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
              >
                Logout
                <IconLogout className="h-4 w-4 text-slate-600" aria-hidden />
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
