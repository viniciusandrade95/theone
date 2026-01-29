"use client";

import Link from "next/link";
import React from "react";
import { useTenant } from "../../lib/tenant";

export function TopBar() {
  const { tenantId } = useTenant();

  return (
    <div className="flex w-full flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xl font-semibold text-slate-900">Dashboard</p>
        <p className="text-sm text-slate-500">
          Welcome back to your workspace. Manage customers and insights.
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          Tenant: {tenantId || "Not set"}
        </div>
        <Link
          href="/dashboard/settings"
          className="text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          Manage tenant
        </Link>
        <div className="flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
            BC
          </span>
          <div className="text-sm">
            <p className="font-semibold text-slate-900">Beauty CRM</p>
            <p className="text-xs text-slate-500">Admin</p>
          </div>
        </div>
      </div>
    </div>
  );
}
