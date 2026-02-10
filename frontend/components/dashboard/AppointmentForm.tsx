"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";

export type AppointmentStatus = "booked" | "completed" | "cancelled" | "no_show";

export type AppointmentFormValues = {
  customer_id: string;
  service_id: string;
  starts_at: string;
  duration_minutes: number;
  status: AppointmentStatus;
  cancelled_reason: string;
  notes: string;
};

export type AppointmentServiceOption = {
  id: string;
  name: string;
  duration_minutes: number;
  is_active?: boolean;
};

export type AppointmentSubmitPayload = {
  customer_id: string;
  location_id: string;
  service_id: string | null;
  starts_at: string;
  ends_at: string;
  status: AppointmentStatus;
  cancelled_reason: string | null;
  notes: string | null;
};

type CustomerOption = {
  id: string;
  name: string;
};

type CustomersResponse = {
  items?: Array<{ id: string; name?: string | null }>;
};

type ConflictItem = {
  id: string;
  starts_at: string;
  ends_at: string;
};

type ErrorPayload = {
  message?: string;
  detail?: string;
  error?: string;
  conflicts?: unknown;
};

type ApiError = {
  response?: {
    status?: number;
    data?: ErrorPayload;
  };
};

type AppointmentFormProps = {
  mode: "create" | "edit";
  values: AppointmentFormValues;
  onChange: (next: AppointmentFormValues) => void;
  onSubmit: (payload: AppointmentSubmitPayload) => Promise<void>;
  services: AppointmentServiceOption[];
  defaultLocationId: string | null;
  customerNameById?: Record<string, string>;
  disabled?: boolean;
  onCancel?: () => void;
  submitLabel?: string;
  submittingLabel?: string;
  cancelLabel?: string;
  conflictHrefForId?: (id: string) => string;
};

const STATUSES: AppointmentStatus[] = ["booked", "completed", "cancelled", "no_show"];

function toLocalDateTimeInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hour = String(value.getHours()).padStart(2, "0");
  const minute = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function toErrorMessage(error: unknown, fallback: string): string {
  const maybe = error as ApiError;
  return maybe?.response?.data?.message || maybe?.response?.data?.detail || maybe?.response?.data?.error || fallback;
}

function parseConflicts(payload: unknown): ConflictItem[] {
  if (!Array.isArray(payload)) {
    return [];
  }
  return payload.flatMap((item) => {
    if (!item || typeof item !== "object") {
      return [];
    }
    const value = item as Record<string, unknown>;
    if (typeof value.id !== "string" || typeof value.starts_at !== "string" || typeof value.ends_at !== "string") {
      return [];
    }
    return [{ id: value.id, starts_at: value.starts_at, ends_at: value.ends_at }];
  });
}

function formatRange(startsAt: string, endsAt: string): string {
  const starts = new Date(startsAt);
  const ends = new Date(endsAt);
  if (Number.isNaN(starts.getTime()) || Number.isNaN(ends.getTime())) {
    return `${startsAt} - ${endsAt}`;
  }
  return `${starts.toLocaleString()} - ${ends.toLocaleString()}`;
}

function defaultConflictHref(id: string): string {
  const encoded = encodeURIComponent(id);
  return appPath(`/dashboard/appointments?appointment_id=${encoded}#appointment-${encoded}`);
}

export function AppointmentForm({
  mode,
  values,
  onChange,
  onSubmit,
  services,
  defaultLocationId,
  customerNameById,
  disabled = false,
  onCancel,
  submitLabel,
  submittingLabel,
  cancelLabel = "Cancel",
  conflictHrefForId,
}: AppointmentFormProps) {
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerOptions, setCustomerOptions] = useState<CustomerOption[]>([]);
  const [isSearchingCustomers, setIsSearchingCustomers] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);

  const effectiveSubmitLabel = submitLabel ?? (mode === "create" ? "Create appointment" : "Save changes");
  const effectiveSubmittingLabel = submittingLabel ?? (mode === "create" ? "Creating..." : "Saving...");

  const serviceById = useMemo(
    () =>
      Object.fromEntries(
        services.map((service) => [
          service.id,
          {
            duration_minutes: service.duration_minutes,
            is_active: service.is_active !== false,
          },
        ]),
      ) as Record<string, { duration_minutes: number; is_active: boolean }>,
    [services],
  );

  const selectedCustomer = useMemo(() => {
    if (!values.customer_id) {
      return null;
    }
    const fromOptions = customerOptions.find((item) => item.id === values.customer_id);
    if (fromOptions) {
      return fromOptions;
    }
    const hintedName = customerNameById?.[values.customer_id];
    return { id: values.customer_id, name: hintedName || values.customer_id };
  }, [customerNameById, customerOptions, values.customer_id]);

  const mergedCustomerOptions = useMemo(() => {
    const byId = new Map<string, CustomerOption>();
    if (selectedCustomer) {
      byId.set(selectedCustomer.id, selectedCustomer);
    }
    for (const option of customerOptions) {
      byId.set(option.id, option);
    }
    return Array.from(byId.values());
  }, [customerOptions, selectedCustomer]);

  const serviceOptions = useMemo(() => {
    return services.filter((service) => service.is_active !== false || service.id === values.service_id);
  }, [services, values.service_id]);

  const computedEndsAt = useMemo(() => {
    if (!values.starts_at || !Number.isFinite(values.duration_minutes) || values.duration_minutes <= 0) {
      return "";
    }
    const startsAt = new Date(values.starts_at);
    if (Number.isNaN(startsAt.getTime())) {
      return "";
    }
    const endsAt = new Date(startsAt.getTime() + values.duration_minutes * 60_000);
    return toLocalDateTimeInput(endsAt);
  }, [values.duration_minutes, values.starts_at]);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(async () => {
      setIsSearchingCustomers(true);
      try {
        const response = await api.get<CustomersResponse>("/crm/customers", {
          params: {
            page: 1,
            page_size: 20,
            query: customerQuery.trim() || undefined,
            sort: "name",
            order: "asc",
          },
        });
        if (!active) {
          return;
        }
        const items = Array.isArray(response.data?.items) ? response.data.items : [];
        setCustomerOptions(
          items
            .filter((item): item is { id: string; name?: string | null } => Boolean(item?.id))
            .map((item) => ({
              id: item.id,
              name: item.name?.trim() || item.id,
            })),
        );
      } catch {
        if (active) {
          setCustomerOptions([]);
        }
      } finally {
        if (active) {
          setIsSearchingCustomers(false);
        }
      }
    }, 300);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [customerQuery]);

  function update(next: AppointmentFormValues) {
    setSubmitError(null);
    setConflicts([]);
    onChange(next);
  }

  function handleServiceChange(serviceId: string) {
    const service = serviceById[serviceId];
    const nextDuration =
      serviceId && service && Number.isFinite(service.duration_minutes) && service.duration_minutes > 0
        ? service.duration_minutes
        : values.duration_minutes;
    update({
      ...values,
      service_id: serviceId,
      duration_minutes: nextDuration,
    });
  }

  async function handleSubmit() {
    if (disabled) {
      return;
    }
    if (!defaultLocationId) {
      setSubmitError("Default location not available yet.");
      return;
    }
    if (!values.customer_id) {
      setSubmitError("Customer is required.");
      return;
    }
    if (!values.starts_at) {
      setSubmitError("Start date/time is required.");
      return;
    }
    if (!Number.isFinite(values.duration_minutes) || values.duration_minutes <= 0) {
      setSubmitError("Duration must be greater than 0.");
      return;
    }

    const startsAt = new Date(values.starts_at);
    if (Number.isNaN(startsAt.getTime())) {
      setSubmitError("Start date/time is invalid.");
      return;
    }

    const endsAt = new Date(startsAt.getTime() + values.duration_minutes * 60_000);
    if (Number.isNaN(endsAt.getTime()) || endsAt <= startsAt) {
      setSubmitError("End date/time must be after start date/time.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setConflicts([]);

    try {
      await onSubmit({
        customer_id: values.customer_id,
        location_id: defaultLocationId,
        service_id: values.service_id || null,
        starts_at: startsAt.toISOString(),
        ends_at: endsAt.toISOString(),
        status: values.status,
        cancelled_reason: values.status === "cancelled" ? values.cancelled_reason.trim() || null : null,
        notes: values.notes.trim() || null,
      });
    } catch (error: unknown) {
      const maybe = error as ApiError;
      if (maybe?.response?.status === 409) {
        const conflictItems = parseConflicts(maybe?.response?.data?.conflicts);
        if (conflictItems.length > 0) {
          setConflicts(conflictItems);
          setSubmitError("Conflicting appointment found. Choose a different time slot.");
        } else {
          setSubmitError("Conflicting appointment found.");
        }
      } else {
        setSubmitError(
          toErrorMessage(error, mode === "create" ? "Unable to create appointment." : "Unable to update appointment."),
        );
      }
      return;
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        void handleSubmit();
      }}
    >
      <input type="hidden" name="location_id" value={defaultLocationId ?? ""} readOnly />

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Customer search
          <Input
            value={customerQuery}
            onChange={(event) => setCustomerQuery(event.target.value)}
            placeholder="Search by name, phone, or email"
          />
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Customer
          <select
            value={values.customer_id}
            onChange={(event) => update({ ...values, customer_id: event.target.value })}
            className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
            required
          >
            <option value="">{isSearchingCustomers ? "Searching customers..." : "Select customer"}</option>
            {mergedCustomerOptions.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Service
          <select
            value={values.service_id}
            onChange={(event) => handleServiceChange(event.target.value)}
            className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
          >
            <option value="">No service</option>
            {serviceOptions.map((service) => (
              <option
                key={service.id}
                value={service.id}
                disabled={service.is_active === false && service.id !== values.service_id}
              >
                {service.name}
                {service.is_active === false ? " (inactive)" : ""}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Status
          <select
            value={values.status}
            onChange={(event) => update({ ...values, status: event.target.value as AppointmentStatus })}
            className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
          >
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Starts at
          <Input
            type="datetime-local"
            value={values.starts_at}
            onChange={(event) => update({ ...values, starts_at: event.target.value })}
            required
          />
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Duration (minutes)
          <Input
            type="number"
            min={1}
            value={values.duration_minutes}
            onChange={(event) =>
              update({
                ...values,
                duration_minutes: Number.isFinite(Number(event.target.value))
                  ? Number(event.target.value)
                  : values.duration_minutes,
              })
            }
            required
          />
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Ends at
          <Input value={computedEndsAt} readOnly />
        </label>

        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Notes
          <Input
            value={values.notes}
            onChange={(event) => update({ ...values, notes: event.target.value })}
            placeholder="Optional notes"
          />
        </label>
      </div>

      {values.status === "cancelled" ? (
        <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
          Cancelled reason
          <Input
            value={values.cancelled_reason}
            onChange={(event) => update({ ...values, cancelled_reason: event.target.value })}
            placeholder="Optional cancellation reason"
          />
        </label>
      ) : null}

      {submitError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</div>
      ) : null}

      {conflicts.length > 0 ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          <p className="font-semibold">Conflicting appointment(s)</p>
          <div className="mt-2 space-y-1">
            {conflicts.map((item) => {
              const href = conflictHrefForId ? conflictHrefForId(item.id) : defaultConflictHref(item.id);
              return (
                <div key={item.id} className="flex flex-wrap items-center justify-between gap-2">
                  <span>{formatRange(item.starts_at, item.ends_at)}</span>
                  <a className="font-semibold text-amber-900 underline" href={href}>
                    Open appointment
                  </a>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={disabled || isSubmitting}>
          {isSubmitting ? effectiveSubmittingLabel : effectiveSubmitLabel}
        </Button>
        {onCancel ? (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            {cancelLabel}
          </Button>
        ) : null}
      </div>
    </form>
  );
}
