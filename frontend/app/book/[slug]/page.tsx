"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type PublicService = {
  id: string;
  name: string;
  duration_minutes: number;
  price_cents: number | null;
};

type PublicLocation = {
  id: string;
  name: string;
  timezone: string;
};

type PublicBookingConfig = {
  slug: string;
  business_name: string;
  contact_phone: string | null;
  contact_email: string | null;
  primary_color: string | null;
  logo_url: string | null;
  services: PublicService[];
  locations: PublicLocation[];
  requires_location: boolean;
};

type AvailabilitySlot = {
  starts_at: string;
  ends_at: string;
  label: string;
};

type AvailabilityResponse = {
  date: string;
  timezone: string;
  slots: AvailabilitySlot[];
};

type CreateBookingResponse = {
  ok: boolean;
  appointment_id: string;
  needs_confirmation: boolean;
};

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

function toErrorMessage(error: unknown, fallback: string): string {
  const data = (error as { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } })?.data;
  return data?.details?.message || data?.message || data?.detail || data?.error || fallback;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const data = (await resp.json().catch(() => null)) as any;
  if (!resp.ok) {
    const error = { status: resp.status, data };
    throw error;
  }
  return data as T;
}

function todayIso(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function PublicBookingPage({ params }: { params: { slug: string } }) {
  const slug = params.slug;

  const [config, setConfig] = useState<PublicBookingConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedServiceId, setSelectedServiceId] = useState<string>("");
  const [selectedLocationId, setSelectedLocationId] = useState<string>("");
  const [date, setDate] = useState<string>(todayIso());

  const [availability, setAvailability] = useState<AvailabilityResponse | null>(null);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [selectedStartsAt, setSelectedStartsAt] = useState<string>("");

  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [note, setNote] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const selectedService = useMemo(() => config?.services.find((s) => s.id === selectedServiceId) ?? null, [config, selectedServiceId]);

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchJson<PublicBookingConfig>(`/public/book/${encodeURIComponent(slug)}`);
        if (!active) return;
        setConfig(data);
        if (data.services.length === 1) {
          setSelectedServiceId(data.services[0].id);
        }
        if (!data.requires_location && data.locations.length === 1) {
          setSelectedLocationId(data.locations[0].id);
        }
      } catch (err) {
        if (active) {
          setError(toErrorMessage((err as any) ?? null, "Unable to load booking page."));
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [slug]);

  useEffect(() => {
    setAvailability(null);
    setSelectedStartsAt("");
  }, [selectedServiceId, selectedLocationId, date]);

  async function loadAvailability() {
    if (!selectedServiceId) {
      setError("Please select a service.");
      return;
    }
    if (config?.requires_location && !selectedLocationId) {
      setError("Please select a location.");
      return;
    }

    setIsLoadingSlots(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("service_id", selectedServiceId);
      params.set("date", date);
      if (selectedLocationId) params.set("location_id", selectedLocationId);
      const data = await fetchJson<AvailabilityResponse>(`/public/book/${encodeURIComponent(slug)}/availability?${params.toString()}`);
      setAvailability(data);
    } catch (err) {
      setError(toErrorMessage((err as any) ?? null, "Unable to load availability."));
    } finally {
      setIsLoadingSlots(false);
    }
  }

  async function submitBooking() {
    if (!selectedServiceId) {
      setError("Please select a service.");
      return;
    }
    if (config?.requires_location && !selectedLocationId) {
      setError("Please select a location.");
      return;
    }
    if (!selectedStartsAt) {
      setError("Please select a time.");
      return;
    }
    if (!customerName.trim()) {
      setError("Name is required.");
      return;
    }
    if (!customerPhone.trim()) {
      setError("Phone is required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const data = await fetchJson<CreateBookingResponse>(`/public/book/${encodeURIComponent(slug)}/appointments`, {
        method: "POST",
        body: JSON.stringify({
          service_id: selectedServiceId,
          starts_at: selectedStartsAt,
          location_id: selectedLocationId || null,
          customer_name: customerName.trim(),
          customer_phone: customerPhone.trim(),
          customer_email: customerEmail.trim() || null,
          note: note.trim() || null,
        }),
      });
      if (data.needs_confirmation) {
        setSuccessMessage("Booking request received. We'll confirm it shortly.");
      } else {
        setSuccessMessage("Booking confirmed. See you soon.");
      }
      setSelectedStartsAt("");
      setCustomerName("");
      setCustomerPhone("");
      setCustomerEmail("");
      setNote("");
    } catch (err) {
      setError(toErrorMessage((err as any) ?? null, "Unable to complete booking."));
    } finally {
      setIsSubmitting(false);
    }
  }

  const headerStyle = useMemo(() => {
    if (!config?.primary_color) return undefined;
    return { borderColor: config.primary_color };
  }, [config?.primary_color]);

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6 px-4 py-8">
      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : error && !config ? (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>
      ) : null}

      {config ? (
        <>
          <Card style={headerStyle} className="border-2">
            <CardHeader className="flex flex-row items-center gap-4">
              {config.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={config.logo_url} alt={config.business_name} className="h-12 w-12 rounded-xl border border-slate-200 object-cover" />
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-900 text-sm font-semibold text-white">
                  {config.business_name.slice(0, 2).toUpperCase()}
                </div>
              )}
              <div className="min-w-0">
                <CardTitle className="truncate">{config.business_name}</CardTitle>
                <CardDescription className="mt-1">
                  {config.contact_phone ? <span className="mr-3">Phone: {config.contact_phone}</span> : null}
                  {config.contact_email ? <span>Email: {config.contact_email}</span> : null}
                </CardDescription>
              </div>
            </CardHeader>
          </Card>

          {successMessage ? (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">{successMessage}</p>
          ) : null}
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

          <Card>
            <CardHeader>
              <CardTitle>Select service</CardTitle>
              <CardDescription>Choose what you want to book.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {config.services.length === 0 ? (
                <p className="text-sm text-slate-500">No services available for online booking.</p>
              ) : (
                <div className="grid gap-2">
                  {config.services.map((s) => {
                    const active = s.id === selectedServiceId;
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setSelectedServiceId(s.id)}
                        className={[
                          "w-full rounded-xl border px-4 py-3 text-left transition",
                          active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white hover:bg-slate-50",
                        ].join(" ")}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate font-semibold">{s.name}</p>
                            <p className={active ? "text-xs text-slate-200" : "text-xs text-slate-500"}>{s.duration_minutes} min</p>
                          </div>
                          <div className={active ? "text-sm font-semibold text-white" : "text-sm font-semibold text-slate-900"}>
                            {s.price_cents !== null ? `$${(s.price_cents / 100).toFixed(2)}` : ""}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Date & time</CardTitle>
              <CardDescription>Pick a day and a time that works for you.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {config.requires_location ? (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Location</p>
                  <select
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={selectedLocationId}
                    onChange={(e) => setSelectedLocationId(e.target.value)}
                  >
                    <option value="">Select a location...</option>
                    {config.locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Date</p>
                  <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                </div>
                <div className="flex items-end">
                  <Button type="button" disabled={isLoadingSlots || !selectedServiceId} onClick={() => void loadAvailability()}>
                    {isLoadingSlots ? "Loading..." : "Show times"}
                  </Button>
                </div>
              </div>

              {availability ? (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">
                    Available times <span className="text-xs font-normal text-slate-500">({availability.timezone})</span>
                  </p>
                  {availability.slots.length === 0 ? (
                    <p className="text-sm text-slate-500">No available times for this day.</p>
                  ) : (
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                      {availability.slots.map((slot) => {
                        const active = slot.starts_at === selectedStartsAt;
                        return (
                          <button
                            key={slot.starts_at}
                            type="button"
                            onClick={() => setSelectedStartsAt(slot.starts_at)}
                            className={[
                              "rounded-lg border px-3 py-2 text-sm font-semibold transition",
                              active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white hover:bg-slate-50",
                            ].join(" ")}
                          >
                            {slot.label}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Your details</CardTitle>
              <CardDescription>We’ll use these details for your appointment.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Name</p>
                  <Input value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Your name" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Phone</p>
                  <Input value={customerPhone} onChange={(e) => setCustomerPhone(e.target.value)} placeholder="+351..." />
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-700">Email (optional)</p>
                <Input value={customerEmail} onChange={(e) => setCustomerEmail(e.target.value)} placeholder="you@email.com" />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-700">Note (optional)</p>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="min-h-[96px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                  placeholder="Anything we should know?"
                />
              </div>

              <Button type="button" disabled={isSubmitting || !selectedServiceId} onClick={() => void submitBooking()} className="w-full">
                {isSubmitting ? "Booking..." : selectedService ? `Book ${selectedService.name}` : "Book now"}
              </Button>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

