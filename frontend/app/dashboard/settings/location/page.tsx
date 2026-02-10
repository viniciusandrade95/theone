"use client";

import { useEffect, useState } from "react";

import { SettingsNav } from "@/components/dashboard/SettingsNav";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { SettingsLocation, SettingsLocationUpdatePayload } from "@/lib/contracts/settings";
import { api } from "@/lib/api";

type LocationFormState = {
  id: string;
  name: string;
  timezone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  postcode: string;
  country: string;
  phone: string;
  email: string;
  allow_overlaps: boolean;
  hours_json: string;
};

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function toFormState(location: SettingsLocation): LocationFormState {
  return {
    id: location.id,
    name: location.name ?? "",
    timezone: location.timezone ?? "UTC",
    address_line1: location.address_line1 ?? "",
    address_line2: location.address_line2 ?? "",
    city: location.city ?? "",
    postcode: location.postcode ?? "",
    country: location.country ?? "",
    phone: location.phone ?? "",
    email: location.email ?? "",
    allow_overlaps: Boolean(location.allow_overlaps),
    hours_json: location.hours_json ? JSON.stringify(location.hours_json, null, 2) : "",
  };
}

export default function SettingsLocationPage() {
  const [form, setForm] = useState<LocationFormState | null>(null);
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
        const location = await api.get<SettingsLocation>("/crm/settings/location");
        if (!active) {
          return;
        }
        setForm(toFormState(location.data));
      } catch (requestError) {
        if (active) {
          setError(toErrorMessage(requestError, "Unable to load location settings."));
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
    if (!form) {
      return;
    }

    let parsedHoursJson: Record<string, unknown> | null = null;
    if (form.hours_json.trim()) {
      try {
        const parsed = JSON.parse(form.hours_json);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          parsedHoursJson = parsed as Record<string, unknown>;
        } else {
          setError("Business hours must be a JSON object.");
          return;
        }
      } catch {
        setError("Business hours JSON is invalid.");
        return;
      }
    }

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload: SettingsLocationUpdatePayload = {
        name: form.name.trim(),
        timezone: form.timezone.trim(),
        address_line1: form.address_line1.trim() || null,
        address_line2: form.address_line2.trim() || null,
        city: form.city.trim() || null,
        postcode: form.postcode.trim() || null,
        country: form.country.trim() || null,
        phone: form.phone.trim() || null,
        email: form.email.trim() || null,
        allow_overlaps: form.allow_overlaps,
        hours_json: parsedHoursJson,
      };

      const response = await api.put<SettingsLocation>("/crm/settings/location", payload);
      setForm(toFormState(response.data));
      setSuccessMessage("Location settings updated.");
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update location settings."));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsNav />

      <Card>
        <CardHeader>
          <CardTitle>Main location</CardTitle>
          <CardDescription>Edit location details and overlap policy for single-location mode.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          {successMessage ? (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{successMessage}</p>
          ) : null}

          {isLoading || !form ? (
            <p className="text-sm text-slate-500">Loading location...</p>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Name
                  <Input
                    value={form.name}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, name: event.target.value } : prev))}
                    required
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Timezone
                  <Input
                    value={form.timezone}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, timezone: event.target.value } : prev))}
                    required
                  />
                </label>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Address line 1
                  <Input
                    value={form.address_line1}
                    onChange={(event) =>
                      setForm((prev) => (prev ? { ...prev, address_line1: event.target.value } : prev))
                    }
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Address line 2
                  <Input
                    value={form.address_line2}
                    onChange={(event) =>
                      setForm((prev) => (prev ? { ...prev, address_line2: event.target.value } : prev))
                    }
                  />
                </label>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  City
                  <Input
                    value={form.city}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, city: event.target.value } : prev))}
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Postcode
                  <Input
                    value={form.postcode}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, postcode: event.target.value } : prev))}
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Country
                  <Input
                    value={form.country}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, country: event.target.value } : prev))}
                  />
                </label>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Phone
                  <Input
                    value={form.phone}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, phone: event.target.value } : prev))}
                    placeholder="+15551234567"
                  />
                </label>
                <label className="space-y-1 text-sm font-medium text-slate-700">
                  Email
                  <Input
                    value={form.email}
                    onChange={(event) => setForm((prev) => (prev ? { ...prev, email: event.target.value } : prev))}
                    placeholder="studio@example.com"
                    type="email"
                  />
                </label>
              </div>

              <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={form.allow_overlaps}
                  onChange={(event) =>
                    setForm((prev) => (prev ? { ...prev, allow_overlaps: event.target.checked } : prev))
                  }
                />
                Allow appointment overlaps
              </label>

              <label className="space-y-1 text-sm font-medium text-slate-700">
                Business hours JSON
                <textarea
                  className="min-h-36 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
                  value={form.hours_json}
                  onChange={(event) => setForm((prev) => (prev ? { ...prev, hours_json: event.target.value } : prev))}
                  placeholder='{"mon":{"open":"09:00","close":"18:00"}}'
                />
              </label>

              <Button type="submit" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save location settings"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
