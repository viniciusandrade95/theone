"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const SETTINGS_ITEMS = [
  { href: "/dashboard/settings/general", label: "General" },
  { href: "/dashboard/settings/calendar", label: "Calendar" },
  { href: "/dashboard/settings/location", label: "Location" },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SettingsNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap items-center gap-2">
      {SETTINGS_ITEMS.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "rounded-lg px-3 py-2 text-sm font-semibold transition",
              active ? "bg-slate-900 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
            ].join(" ")}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
