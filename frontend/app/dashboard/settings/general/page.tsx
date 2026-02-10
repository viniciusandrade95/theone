"use client";

import { useEffect, useState } from "react";

import { SettingsNav } from "@/components/dashboard/SettingsNav";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { TenantSettings, TenantSettingsUpdatePayload } from "@/lib/contracts/settings";
import { api } from "@/lib/api";

type GeneralTenantSettings = Pick<
  TenantSettings,
  "business_name" | "default_timezone" | "currency" | "primary_color" | "logo_url"
>;

type GeneralFormState = {
  business_name: string;
  default_timezone: string;
  currency: string;
  primary_color: string;
  logo_url: string;
};

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string; error?: string } } })?.response;
  return response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function toFormState(settings: GeneralTenantSettings): GeneralFormState {
  return {
    business_name: settings.business_name ?? "",
    default_timezone: settings.default_timezone ?? "UTC",
    currency: settings.currency ?? "USD",
    primary_color: settings.primary_color ?? "",
    logo_url: settings.logo_url ?? "",
  };
}

export default function SettingsGeneralPage() {
  const [form, setForm] = useState<GeneralFormState>({
    business_name: "",
    default_timezone: "UTC",
    currency: "USD",
    primary_color: "",
    logo_url: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<TenantSettings>("/crm/settings");
        if (!active) {
          return;
        }
        setForm(toFormState(response.data));
      } catch (requestError) {
        if (active) {
          setError(toErrorMessage(requestError, "Unable to load settings."));
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload: TenantSettingsUpdatePayload = {
        business_name: form.business_name.trim() || null,
        default_timezone: form.default_timezone.trim(),
        currency: form.currency.trim().toUpperCase(),
        primary_color: form.primary_color.trim() || null,
        logo_url: form.logo_url.trim() || null,
      };
      const response = await api.put<TenantSettings>("/crm/settings", payload);
      setForm(toFormState(response.data));
      setSuccessMessage("General settings updated.");
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update settings."));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsNav />

      <Card>
        <CardHeader>
          <CardTitle>General settings</CardTitle>
          <CardDescription>Business profile and default workspace values.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          {successMessage ? (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{successMessage}</p>
          ) : null}

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading settings...</p>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <label className="space-y-1 text-sm font-medium text-slate-700">
                Business name
                <Input
                  value={form.business_name}
                  onChange={(event) => setForm((prev) => ({ ...prev, business_name: event.target.value }))}
                  placeholder="The One Beauty"
                />
              </label>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Timezone
                  <Input
                    value={form.default_timezone}
                    onChange={(event) => setForm((prev) => ({ ...prev, default_timezone: event.target.value }))}
                    placeholder="America/New_York"
                    required
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Currency
                  <Input
                    value={form.currency}
                    onChange={(event) => setForm((prev) => ({ ...prev, currency: event.target.value }))}
                    placeholder="USD"
                    required
                  />
                </label>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Primary color
                  <Input
                    value={form.primary_color}
                    onChange={(event) => setForm((prev) => ({ ...prev, primary_color: event.target.value }))}
                    placeholder="#0f172a"
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Logo URL
                  <Input
                    value={form.logo_url}
                    onChange={(event) => setForm((prev) => ({ ...prev, logo_url: event.target.value }))}
                    placeholder="https://cdn.example.com/logo.png"
                  />
                </label>
              </div>

              <Button type="submit" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save general settings"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
