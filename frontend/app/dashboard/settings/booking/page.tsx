"use client";

import { useEffect, useMemo, useState } from "react";

import { SettingsNav } from "@/components/dashboard/SettingsNav";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { BookingSettings, BookingSettingsUpdatePayload } from "@/lib/contracts/booking";

type FormState = {
  booking_enabled: boolean;
  booking_slug: string;
  public_business_name: string;
  public_contact_phone: string;
  public_contact_email: string;
  min_booking_notice_minutes: string;
  max_booking_notice_days: string;
  auto_confirm_bookings: boolean;
};

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function toFormState(settings: BookingSettings): FormState {
  return {
    booking_enabled: settings.booking_enabled,
    booking_slug: settings.booking_slug ?? "",
    public_business_name: settings.public_business_name ?? "",
    public_contact_phone: settings.public_contact_phone ?? "",
    public_contact_email: settings.public_contact_email ?? "",
    min_booking_notice_minutes: String(settings.min_booking_notice_minutes ?? 60),
    max_booking_notice_days: String(settings.max_booking_notice_days ?? 90),
    auto_confirm_bookings: settings.auto_confirm_bookings,
  };
}

function parseIntSafe(value: string): number | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return Math.trunc(parsed);
}

export default function SettingsBookingPage() {
  const [form, setForm] = useState<FormState>({
    booking_enabled: false,
    booking_slug: "",
    public_business_name: "",
    public_contact_phone: "",
    public_contact_email: "",
    min_booking_notice_minutes: "60",
    max_booking_notice_days: "90",
    auto_confirm_bookings: true,
  });
  const [loaded, setLoaded] = useState<BookingSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const publicLink = useMemo(() => {
    const slug = form.booking_slug.trim().toLowerCase();
    if (!slug) return null;
    return `/book/${slug}`;
  }, [form.booking_slug]);

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<BookingSettings>("/crm/booking/settings");
        if (!active) return;
        setLoaded(response.data);
        setForm(toFormState(response.data));
      } catch (requestError) {
        if (active) {
          setError(toErrorMessage(requestError, "Unable to load booking settings."));
        }
      } finally {
        if (active) setIsLoading(false);
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

    const minNotice = parseIntSafe(form.min_booking_notice_minutes);
    const maxDays = parseIntSafe(form.max_booking_notice_days);
    if (minNotice === null || minNotice < 0) {
      setIsSaving(false);
      setError("Minimum notice must be a valid number (minutes).");
      return;
    }
    if (maxDays === null || maxDays < 1) {
      setIsSaving(false);
      setError("Maximum notice must be a valid number (days).");
      return;
    }

    try {
      const payload: BookingSettingsUpdatePayload = {
        booking_enabled: form.booking_enabled,
        booking_slug: form.booking_slug.trim().toLowerCase() || null,
        public_business_name: form.public_business_name.trim() || null,
        public_contact_phone: form.public_contact_phone.trim() || null,
        public_contact_email: form.public_contact_email.trim().toLowerCase() || null,
        min_booking_notice_minutes: minNotice,
        max_booking_notice_days: maxDays,
        auto_confirm_bookings: form.auto_confirm_bookings,
      };
      const response = await api.put<BookingSettings>("/crm/booking/settings", payload);
      setLoaded(response.data);
      setForm(toFormState(response.data));
      setSuccessMessage("Booking settings updated.");
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update booking settings."));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsNav />

      <Card>
        <CardHeader>
          <CardTitle>Online booking</CardTitle>
          <CardDescription>Public booking page for your business.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          {successMessage ? (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{successMessage}</p>
          ) : null}

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading booking settings...</p>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <input
                  type="checkbox"
                  checked={form.booking_enabled}
                  onChange={(event) => setForm((prev) => ({ ...prev, booking_enabled: event.target.checked }))}
                />
                Enable online booking
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Public slug</p>
                  <Input
                    value={form.booking_slug}
                    onChange={(event) => setForm((prev) => ({ ...prev, booking_slug: event.target.value }))}
                    placeholder="my-studio"
                  />
                  {publicLink ? (
                    <p className="text-xs text-slate-500">
                      Public page: <span className="font-mono">{publicLink}</span>
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Public business name</p>
                  <Input
                    value={form.public_business_name}
                    onChange={(event) => setForm((prev) => ({ ...prev, public_business_name: event.target.value }))}
                    placeholder="Beauty Studio"
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Contact phone (optional)</p>
                  <Input
                    value={form.public_contact_phone}
                    onChange={(event) => setForm((prev) => ({ ...prev, public_contact_phone: event.target.value }))}
                    placeholder="+351..."
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Contact email (optional)</p>
                  <Input
                    value={form.public_contact_email}
                    onChange={(event) => setForm((prev) => ({ ...prev, public_contact_email: event.target.value }))}
                    placeholder="hello@..."
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Min notice (minutes)</p>
                  <Input
                    value={form.min_booking_notice_minutes}
                    onChange={(event) => setForm((prev) => ({ ...prev, min_booking_notice_minutes: event.target.value }))}
                    placeholder="60"
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Max notice (days)</p>
                  <Input
                    value={form.max_booking_notice_days}
                    onChange={(event) => setForm((prev) => ({ ...prev, max_booking_notice_days: event.target.value }))}
                    placeholder="90"
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Auto confirm</p>
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={form.auto_confirm_bookings}
                      onChange={(event) => setForm((prev) => ({ ...prev, auto_confirm_bookings: event.target.checked }))}
                    />
                    Create appointments as confirmed (booked)
                  </label>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving..." : "Save"}
                </Button>
                {loaded?.public_url_path ? (
                  <a className="text-sm font-semibold text-slate-700 underline" href={loaded.public_url_path} target="_blank" rel="noreferrer">
                    Open public page
                  </a>
                ) : null}
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

