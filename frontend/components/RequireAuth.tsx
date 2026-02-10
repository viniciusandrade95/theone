"use client";

import { useEffect, useState } from "react";
import { requireAuthOrRedirect } from "@/lib/requireAuth";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(requireAuthOrRedirect());
  }, []);

  if (!ready) {
    return null;
  }

  return <>{children}</>;
}
