"use client";

import { useEffect, useMemo, useState } from "react";
import { API_ERROR_EVENT } from "@/lib/api";

type ApiErrorDetail = {
  status: number;
  message: string;
  payload?: unknown;
};

type ConflictPayload = {
  conflicts?: Array<{ id: string; starts_at: string; ends_at: string }>;
};

export function ApiErrorBanner() {
  const [notice, setNotice] = useState<ApiErrorDetail | null>(null);

  useEffect(() => {
    const onApiError = (event: Event) => {
      const custom = event as CustomEvent<ApiErrorDetail>;
      setNotice(custom.detail);
    };
    window.addEventListener(API_ERROR_EVENT, onApiError as EventListener);
    return () => window.removeEventListener(API_ERROR_EVENT, onApiError as EventListener);
  }, []);

  useEffect(() => {
    if (!notice) {
      return;
    }
    const timer = window.setTimeout(() => setNotice(null), 7000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const conflicts = useMemo(() => {
    const payload = notice?.payload as ConflictPayload | undefined;
    return Array.isArray(payload?.conflicts) ? payload.conflicts.slice(0, 3) : [];
  }, [notice]);

  if (!notice) {
    return null;
  }

  const isConflict = notice.status === 409;

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 w-full max-w-md">
      <div className="pointer-events-auto rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 shadow-lg">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold">{isConflict ? "Conflict detected" : "Not authorized"}</p>
            <p className="mt-1">{notice.message}</p>
            {isConflict && conflicts.length > 0 ? (
              <div className="mt-2 space-y-1 text-xs text-amber-800">
                {conflicts.map((item) => (
                  <div key={item.id}>
                    {new Date(item.starts_at).toLocaleString()} - {new Date(item.ends_at).toLocaleString()}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          <button
            type="button"
            className="rounded-md border border-amber-300 px-2 py-1 text-xs hover:bg-amber-100"
            onClick={() => setNotice(null)}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
