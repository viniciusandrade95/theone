"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-errors";

export type DefaultLocation = {
  id: string;
  name: string;
  timezone: string;
  allow_overlaps: boolean;
  hours_json: Record<string, unknown> | null;
};

type DefaultLocationContextValue = {
  defaultLocation: DefaultLocation | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

const DefaultLocationContext = createContext<DefaultLocationContextValue | null>(null);

export function DefaultLocationProvider({ children }: { children: React.ReactNode }) {
  const [defaultLocation, setDefaultLocation] = useState<DefaultLocation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<DefaultLocation>("/crm/locations/default");
      setDefaultLocation(response.data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to load default location."));
      setDefaultLocation(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({
      defaultLocation,
      isLoading,
      error,
      refresh,
    }),
    [defaultLocation, error, isLoading, refresh],
  );

  return <DefaultLocationContext.Provider value={value}>{children}</DefaultLocationContext.Provider>;
}

export function useDefaultLocation() {
  const context = useContext(DefaultLocationContext);
  if (!context) {
    throw new Error("useDefaultLocation must be used inside DefaultLocationProvider");
  }
  return context;
}
