"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { clearAuth } from "@/lib/auth";
import { appPath } from "@/lib/paths";
const nav = [
  { href: appPath("/dashboard"), label: "Home" },
  { href: appPath("/dashboard/customers"), label: "Customers" },
  { href: appPath("/dashboard/appointments"), label: "Appointments" },
  { href: appPath("/dashboard/services"), label: "Services" },

];

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex">
        <aside className="hidden md:flex md:w-64 md:flex-col border-r border-slate-200 bg-white">
          <div className="px-5 py-4 border-b border-slate-200">
            <div className="text-lg font-semibold text-slate-900">CRM</div>
            <div className="text-xs text-slate-500">MVP</div>
          </div>

          <nav className="p-2">
            {nav.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "block rounded-xl px-3 py-2 text-sm font-medium",
                    active
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-100",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto p-4 border-t border-slate-200">
            <button
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50"
              onClick={() => {
                clearAuth();
                window.location.assign(appPath("/login"));

              }}
            >
              Logout
            </button>
          </div>
        </aside>

        <main className="flex-1">
          <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
            <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
              <div className="md:hidden text-sm font-semibold text-slate-900">CRM</div>

              <button
                className="md:hidden rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50"
                onClick={() => {
                  clearAuth();
                  window.location.assign(appPath("/login"));

                }}
              >
                Logout
              </button>

              <div className="hidden md:block text-sm text-slate-600">
                Dashboard
              </div>
            </div>
          </header>

          <div className="mx-auto max-w-6xl p-4">{children}</div>
        </main>
      </div>
    </div>
  );
}
