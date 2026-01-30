import Link from "next/link";
import React from "react";

const navItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Customers", href: "/dashboard/customers" },
  { label: "Analytics", href: "/dashboard/analytics" },
  { label: "WhatsApp Accounts", href: "/dashboard/admin/whatsapp-accounts" },
  { label: "Settings", href: "/dashboard/settings" },
  { label: "Logout", href: "/logout" },
];

export function Sidebar() {
  return (
    <div className="space-y-8">
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Enterprise</p>
        <h2 className="text-lg font-semibold">Beauty CRM</h2>
      </div>
      <nav className="grid gap-3 text-sm">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-lg px-3 py-2 text-slate-200 transition hover:bg-slate-900 hover:text-white"
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-xs text-slate-300">
        <p className="font-semibold text-slate-100">Status</p>
        <p className="mt-2">Foundation phase complete.</p>
      </div>
    </div>
  );
}
