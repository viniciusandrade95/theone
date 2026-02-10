"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  AppointmentForm,
  type AppointmentFormValues,
  type AppointmentServiceOption,
  type AppointmentStatus,
  type AppointmentSubmitPayload,
} from "@/components/dashboard/AppointmentForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useDefaultLocation } from "@/lib/default-location";
import { appPath } from "@/lib/paths";

type Customer = {
  id: string;
  name: string;
};

type Appointment = {
  id: string;
  customer_id: string;
  location_id: string;
  service_id: string | null;
  starts_at: string;
  ends_at: string;
  status: AppointmentStatus;
  cancelled_reason: string | null;
  notes: string | null;
  created_at: string;
};

type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

const PAGE_SIZE = 25;
const STATUSES: Array<"all" | AppointmentStatus> = ["all", "booked", "completed", "cancelled", "no_show"];

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleString();
}

function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function toLocalDateTimeInput(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function toIsoRange(fromDate: string, toDate: string): { from_dt: string; to_dt: string } | null {
  if (!fromDate || !toDate) {
    return null;
  }
  const from = new Date(`${fromDate}T00:00:00`);
  const toExclusive = new Date(`${toDate}T00:00:00`);
  toExclusive.setDate(toExclusive.getDate() + 1);
  if (Number.isNaN(from.getTime()) || Number.isNaN(toExclusive.getTime()) || from >= toExclusive) {
    return null;
  }
  return { from_dt: from.toISOString(), to_dt: toExclusive.toISOString() };
}

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function initialForm(defaultCustomerId: string): AppointmentFormValues {
  return {
    customer_id: defaultCustomerId,
    service_id: "",
    starts_at: "",
    duration_minutes: 60,
    status: "booked",
    cancelled_reason: "",
    notes: "",
  };
}

function formFromAppointment(appointment: Appointment): AppointmentFormValues {
  const startsAt = new Date(appointment.starts_at);
  const endsAt = new Date(appointment.ends_at);
  const rawDuration = Math.round((endsAt.getTime() - startsAt.getTime()) / 60_000);
  const safeDuration = Number.isFinite(rawDuration) && rawDuration > 0 ? rawDuration : 60;

  return {
    customer_id: appointment.customer_id,
    service_id: appointment.service_id ?? "",
    starts_at: toLocalDateTimeInput(appointment.starts_at),
    duration_minutes: safeDuration,
    status: appointment.status,
    cancelled_reason: appointment.cancelled_reason ?? "",
    notes: appointment.notes ?? "",
  };
}

function conflictHref(appointmentId: string): string {
  const encoded = encodeURIComponent(appointmentId);
  return appPath(`/dashboard/appointments?appointment_id=${encoded}#appointment-${encoded}`);
}

export default function AppointmentsPage() {
  const searchParams = useSearchParams();
  const presetCustomerId = searchParams.get("customer_id") ?? "";
  const focusAppointmentId = searchParams.get("appointment_id") ?? "";

  const { defaultLocation, isLoading: isLoadingDefaultLocation } = useDefaultLocation();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<AppointmentServiceOption[]>([]);

  const [items, setItems] = useState<Appointment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [reloadNonce, setReloadNonce] = useState(0);

  const [fromDate, setFromDate] = useState(() => {
    const now = new Date();
    now.setDate(now.getDate() - 7);
    return isoDate(now);
  });
  const [toDate, setToDate] = useState(() => {
    const now = new Date();
    now.setDate(now.getDate() + 14);
    return isoDate(now);
  });

  const [statusFilter, setStatusFilter] = useState<"all" | AppointmentStatus>("all");
  const [customerSearchInput, setCustomerSearchInput] = useState("");
  const [customerSearch, setCustomerSearch] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [customerIdFilter, setCustomerIdFilter] = useState(presetCustomerId);

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<AppointmentFormValues>(() => initialForm(presetCustomerId));

  const [editing, setEditing] = useState<Appointment | null>(null);
  const [editForm, setEditForm] = useState<AppointmentFormValues>(initialForm(presetCustomerId));

  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoOpenedFocusId, setAutoOpenedFocusId] = useState<string | null>(null);

  const customerNameById = useMemo(
    () => Object.fromEntries(customers.map((customer) => [customer.id, customer.name])),
    [customers],
  );

  const serviceNameById = useMemo(
    () => Object.fromEntries(services.map((service) => [service.id, service.name])),
    [services],
  );

  useEffect(() => {
    setCreateForm((prev) => ({ ...prev, customer_id: presetCustomerId || prev.customer_id }));
    setCustomerIdFilter(presetCustomerId);
  }, [presetCustomerId]);

  useEffect(() => {
    const timer = setTimeout(() => setCustomerSearch(customerSearchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [customerSearchInput]);

  useEffect(() => {
    setPage(1);
  }, [fromDate, toDate, statusFilter, customerSearch, serviceFilter, customerIdFilter]);

  useEffect(() => {
    let active = true;

    async function loadReferences() {
      try {
        const [customersResponse, servicesResponse] = await Promise.all([
          api.get<Paginated<Customer>>("/crm/customers", {
            params: { page: 1, page_size: 200, sort: "name", order: "asc" },
          }),
          api.get<Paginated<AppointmentServiceOption>>("/crm/services", {
            params: { page: 1, page_size: 200, include_inactive: true, sort: "name", order: "asc" },
          }),
        ]);

        if (!active) {
          return;
        }

        setCustomers(customersResponse.data?.items ?? []);
        setServices(servicesResponse.data?.items ?? []);
      } catch {
        // list fetch below provides visible error
      }
    }

    void loadReferences();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadAppointments() {
      const range = toIsoRange(fromDate, toDate);
      if (!range) {
        setLoadError("Choose a valid date range.");
        setItems([]);
        setTotal(0);
        return;
      }
      if (!defaultLocation?.id) {
        if (!isLoadingDefaultLocation) {
          setLoadError("Default location is not available.");
        }
        setItems([]);
        setTotal(0);
        return;
      }

      setIsLoading(true);
      setLoadError(null);

      try {
        const response = await api.get<Paginated<Appointment>>("/crm/appointments", {
          params: {
            page,
            page_size: PAGE_SIZE,
            from_dt: range.from_dt,
            to_dt: range.to_dt,
            status: statusFilter === "all" ? undefined : statusFilter,
            query: customerSearch || undefined,
            customer_id: customerIdFilter || undefined,
            service_id: serviceFilter || undefined,
            location_id: defaultLocation.id,
            sort: "starts_at",
            order: "asc",
          },
        });

        if (!active) {
          return;
        }

        setItems(response.data?.items ?? []);
        setTotal(response.data?.total ?? 0);
      } catch (requestError) {
        if (!active) {
          return;
        }
        setLoadError(toErrorMessage(requestError, "Unable to load appointments."));
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadAppointments();

    return () => {
      active = false;
    };
  }, [
    page,
    fromDate,
    toDate,
    statusFilter,
    customerSearch,
    serviceFilter,
    customerIdFilter,
    defaultLocation?.id,
    isLoadingDefaultLocation,
    reloadNonce,
  ]);

  useEffect(() => {
    if (!focusAppointmentId) {
      setAutoOpenedFocusId(null);
      return;
    }
    if (autoOpenedFocusId === focusAppointmentId) {
      return;
    }
    const target = items.find((item) => item.id === focusAppointmentId);
    if (!target) {
      return;
    }
    openEdit(target);
    setAutoOpenedFocusId(focusAppointmentId);
  }, [autoOpenedFocusId, focusAppointmentId, items]);

  async function handleCreate(payload: AppointmentSubmitPayload) {
    await api.post("/crm/appointments", payload);
    setCreateForm(initialForm(customerIdFilter || presetCustomerId));
    setShowCreate(false);
    setPage(1);
    setReloadNonce((prev) => prev + 1);
  }

  function openEdit(appointment: Appointment) {
    setEditing(appointment);
    setEditForm(formFromAppointment(appointment));
  }

  async function handleSaveEdit(payload: AppointmentSubmitPayload) {
    if (!editing) {
      return;
    }
    await api.patch(`/crm/appointments/${editing.id}`, payload);
    setEditing(null);
    setPage(1);
    setReloadNonce((prev) => prev + 1);
  }

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Appointments</h1>
          <p className="text-sm text-slate-500">Filter by date range, status, and customer.</p>
        </div>
        <Button type="button" onClick={() => setShowCreate((open) => !open)}>
          {showCreate ? "Close create" : "Create appointment"}
        </Button>
      </div>

      {showCreate ? (
        <Card>
          <CardHeader>
            <CardTitle>Create appointment</CardTitle>
          </CardHeader>
          <CardContent>
            <AppointmentForm
              mode="create"
              values={createForm}
              onChange={setCreateForm}
              onSubmit={handleCreate}
              services={services}
              defaultLocationId={defaultLocation?.id ?? null}
              customerNameById={customerNameById}
              disabled={isLoadingDefaultLocation}
              onCancel={() => setShowCreate(false)}
              submitLabel="Create"
              submittingLabel="Creating..."
              conflictHrefForId={conflictHref}
            />
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
              From
              <Input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
              To
              <Input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
              Status
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as "all" | AppointmentStatus)}
                className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
              >
                {STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status === "all" ? "All" : status}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
              Customer search
              <Input
                value={customerSearchInput}
                onChange={(event) => setCustomerSearchInput(event.target.value)}
                placeholder="Search customer"
              />
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase text-slate-500">
              Service (optional)
              <select
                value={serviceFilter}
                onChange={(event) => setServiceFilter(event.target.value)}
                className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
              >
                <option value="">All services</option>
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {customerIdFilter ? (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span>Quick filter by customer: {customerNameById[customerIdFilter] ?? customerIdFilter}</span>
              <Button type="button" variant="secondary" onClick={() => setCustomerIdFilter("")}>Clear</Button>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appointments</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {loadError ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{loadError}</div>
          ) : null}

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Starts</th>
                  <th className="px-4 py-3 font-semibold">Ends</th>
                  <th className="px-4 py-3 font-semibold">Customer</th>
                  <th className="px-4 py-3 font-semibold">Service</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Created at</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={6}>
                      Loading appointments...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={6}>
                      No appointments found for current filters.
                    </td>
                  </tr>
                ) : (
                  items.map((appointment) => {
                    const isFocused = appointment.id === focusAppointmentId;
                    return (
                      <tr
                        id={`appointment-${appointment.id}`}
                        key={appointment.id}
                        className={`cursor-pointer hover:bg-slate-50 ${isFocused ? "bg-amber-50" : ""}`}
                        onClick={() => openEdit(appointment)}
                      >
                        <td className="px-4 py-3 text-slate-700">{formatDateTime(appointment.starts_at)}</td>
                        <td className="px-4 py-3 text-slate-700">{formatDateTime(appointment.ends_at)}</td>
                        <td className="px-4 py-3 text-slate-700">
                          {customerNameById[appointment.customer_id] ?? appointment.customer_id}
                        </td>
                        <td className="px-4 py-3 text-slate-700">
                          {appointment.service_id ? serviceNameById[appointment.service_id] ?? appointment.service_id : "-"}
                        </td>
                        <td className="px-4 py-3 capitalize text-slate-700">{appointment.status}</td>
                        <td className="px-4 py-3 text-slate-700">{formatDateTime(appointment.created_at)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">{total} appointment(s)</p>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                disabled={page <= 1 || isLoading}
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                variant="secondary"
                disabled={page >= totalPages || isLoading}
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit appointment</CardTitle>
          </CardHeader>
          <CardContent>
            <AppointmentForm
              mode="edit"
              values={editForm}
              onChange={setEditForm}
              onSubmit={handleSaveEdit}
              services={services}
              defaultLocationId={defaultLocation?.id ?? editing.location_id}
              customerNameById={customerNameById}
              onCancel={() => setEditing(null)}
              submitLabel="Save changes"
              submittingLabel="Saving..."
              conflictHrefForId={conflictHref}
            />
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
