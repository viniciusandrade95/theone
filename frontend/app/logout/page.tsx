"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { clearAuth } from "../../lib/auth";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    clearAuth();
    router.replace("/login");
  }, [router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 text-sm text-slate-600 shadow-sm">
        Signing you out...
      </div>
    </main>
  );
}
