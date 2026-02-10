"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Calendar", href: "/dashboard/calendar" },
  { label: "Appointments", href: "/dashboard/appointments" },
  { label: "Customers", href: "/dashboard/customers" },
  { label: "Services", href: "/dashboard/services" },
  { label: "Analytics", href: "/dashboard/analytics" },
  { label: "Settings", href: "/dashboard/settings" },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="hidden border-r border-slate-200 bg-white lg:flex lg:w-64 lg:flex-col">
      <div className="border-b border-slate-200 px-5 py-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Business</p>
        <h1 className="text-lg font-semibold text-slate-900">Beauty CRM</h1>
      </div>
      <nav className="flex-1 p-3">
        {navItems.map((item) => {
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "mb-1 block rounded-xl px-3 py-2 text-sm font-medium transition",
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900",
              ].join(" ")}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-slate-200 px-5 py-4 text-xs text-slate-500">
        Single-location mode
      </div>
    </aside>
  );
}
