"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

import { clearAuth } from "@/lib/auth";
import { appPath } from "@/lib/paths";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { IconX, IconLogout } from "@/components/ui/icons";

const navItems = [
  { label: "Overview", href: "/dashboard" },
  { label: "Calendar", href: "/dashboard/calendar" },
  { label: "Appointments", href: "/dashboard/appointments" },
  { label: "Customers", href: "/dashboard/customers" },
  { label: "Services", href: "/dashboard/services" },
  { label: "Outbound", href: "/dashboard/outbound/templates" },
  { label: "Analytics", href: "/dashboard/analytics" },
  { label: "Assistant", href: "/dashboard/assistant" },
  { label: "Settings", href: "/dashboard/settings" },
];

function isActive(pathname: string, href: string) {
  if (href === "/dashboard") {
    return pathname === "/dashboard";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MobileNav({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const pathname = usePathname();
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const prevPathnameRef = useRef<string>(pathname);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  useEffect(() => {
    if (!open) {
      prevPathnameRef.current = pathname;
      return;
    }
    if (prevPathnameRef.current !== pathname) {
      onOpenChange(false);
    }
    prevPathnameRef.current = pathname;
  }, [open, onOpenChange, pathname]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 lg:hidden" aria-hidden={!open}>
      <button
        type="button"
        aria-label="Close navigation"
        className="absolute inset-0 cursor-default bg-slate-900/40"
        onClick={() => onOpenChange(false)}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
        className="absolute left-0 top-0 h-full w-[82%] max-w-sm overflow-y-auto bg-white shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Business</p>
            <p className="text-base font-semibold text-slate-900">Beauty CRM</p>
          </div>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            ref={closeButtonRef}
            className="rounded-lg border border-slate-200 p-2 text-slate-700 transition-colors duration-200 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
            aria-label="Close menu"
          >
            <IconX className="h-5 w-5" />
          </button>
        </div>

        <nav className="p-3">
          {navItems.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => onOpenChange(false)}
                className={cn(
                  "mb-1 block rounded-xl px-3 py-3 text-sm font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2",
                  active ? "bg-brand-600 text-white" : "text-slate-700 hover:bg-slate-100 hover:text-slate-900",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-slate-200 p-4">
          <Button
            type="button"
            variant="secondary"
            className="w-full justify-between"
            onClick={() => {
              clearAuth();
              window.location.assign(appPath("/login"));
            }}
          >
            Logout
            <IconLogout className="h-4 w-4 text-slate-600" aria-hidden />
          </Button>
        </div>
      </div>
    </div>
  );
}
