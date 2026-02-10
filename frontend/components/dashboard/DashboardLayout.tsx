"use client";

import { ApiErrorBanner } from "@/components/dashboard/ApiErrorBanner";
import { SidebarNav } from "@/components/dashboard/SidebarNav";
import { TopBar } from "@/components/dashboard/TopBar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-[256px_1fr]">
      <SidebarNav />

      <div className="min-h-screen">
        <TopBar />
        <main className="px-4 py-6 sm:px-6">{children}</main>
      </div>

      <ApiErrorBanner />
    </div>
  );
}
