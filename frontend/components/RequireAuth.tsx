"use client";

import { useEffect } from "react";
import { requireAuthOrRedirect } from "@/lib/requireAuth";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    requireAuthOrRedirect();
  }, []);

  return <>{children}</>;
}
