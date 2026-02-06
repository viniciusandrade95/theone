"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Me = {
  user_id: string;
  tenant_id: string;
  email: string;
};

export default function DashboardHome() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const resp = await api.get<Me>("/auth/me");
        setMe(resp.data);
      } catch (err: any) {
        const msg =
          err?.response?.data?.message ||
          err?.response?.data?.detail ||
          err?.response?.data?.error ||
          "Failed to load /auth/me";
        setError(String(msg));
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        <div className="text-lg font-semibold text-slate-900">
          Dashboard ✅
        </div>
        <div className="mt-2 text-sm text-slate-600">
          If you can see your email + tenant below, auth headers and RLS context are working.
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        {!me ? (
          <div className="text-sm text-slate-600">Loading /auth/me...</div>
        ) : (
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-slate-600">Email:</span>{" "}
              <span className="font-medium text-slate-900">{me.email}</span>
            </div>
            <div>
              <span className="text-slate-600">Tenant:</span>{" "}
              <span className="font-mono text-xs text-slate-900">{me.tenant_id}</span>
            </div>
            <div>
              <span className="text-slate-600">User:</span>{" "}
              <span className="font-mono text-xs text-slate-900">{me.user_id}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
