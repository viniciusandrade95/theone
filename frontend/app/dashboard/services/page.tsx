"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Service = {
  id: string;
  name: string;
  price_cents: number;
  duration_minutes: number;
  is_active: boolean;
};

type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

type FormState = {
  name: string;
  price_cents: string;
  duration_minutes: string;
};

const PAGE_SIZE = 25;

function parseMoneyCents(value: string): number | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return null;
  }
  return Math.trunc(parsed);
}

function parseDuration(value: string): number | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }
  return Math.trunc(parsed);
}

function normalizeServiceForm(form: FormState): { name: string; price_cents: number; duration_minutes: number } | null {
  const name = form.name.trim();
  const priceCents = parseMoneyCents(form.price_cents);
  const durationMinutes = parseDuration(form.duration_minutes);

  if (!name || priceCents === null || durationMinutes === null) {
    return null;
  }

  return {
    name,
    price_cents: priceCents,
    duration_minutes: durationMinutes,
  };
}

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

export default function ServicesPage() {
  const [items, setItems] = useState<Service[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  const [createForm, setCreateForm] = useState<FormState>({
    name: "",
    price_cents: "0",
    duration_minutes: "30",
  });

  const [editing, setEditing] = useState<Service | null>(null);
  const [editForm, setEditForm] = useState<FormState>({
    name: "",
    price_cents: "0",
    duration_minutes: "30",
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
    }, 350);
    return () => clearTimeout(timeout);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const loadServices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await api.get<Paginated<Service>>("/crm/services", {
        params: {
          page,
          page_size: PAGE_SIZE,
          include_inactive: true,
          query: debouncedSearch || undefined,
          sort: "name",
          order: "asc",
        },
      });
      setItems(resp.data.items ?? []);
      setTotal(resp.data.total ?? 0);
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to load services."));
    } finally {
      setIsLoading(false);
    }
  }, [page, debouncedSearch]);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  async function createService() {
    const payload = normalizeServiceForm(createForm);
    if (!payload) {
      setError("Enter a valid name, duration (> 0), and price (>= 0).");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await api.post("/crm/services", payload);
      setCreateForm({ name: "", price_cents: "0", duration_minutes: "30" });
      await loadServices();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to create service."));
    } finally {
      setIsSaving(false);
    }
  }

  function beginEdit(service: Service) {
    setEditing(service);
    setEditForm({
      name: service.name,
      price_cents: String(service.price_cents),
      duration_minutes: String(service.duration_minutes),
    });
  }

  async function saveEdit() {
    if (!editing) {
      return;
    }

    const payload = normalizeServiceForm(editForm);
    if (!payload) {
      setError("Enter a valid name, duration (> 0), and price (>= 0).");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await api.patch(`/crm/services/${editing.id}`, payload);
      setEditing(null);
      await loadServices();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update service."));
    } finally {
      setIsSaving(false);
    }
  }

  async function toggleActive(service: Service) {
    setIsSaving(true);
    setError(null);
    try {
      await api.patch(`/crm/services/${service.id}`, { is_active: !service.is_active });
      await loadServices();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to toggle service."));
    } finally {
      setIsSaving(false);
    }
  }

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Services</h1>
        <p className="text-sm text-slate-500">Create, edit, and manage active/inactive services.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create service</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <Input
              value={createForm.name}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="Service name"
            />
            <Input
              type="number"
              min={0}
              value={createForm.price_cents}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, price_cents: event.target.value }))}
              placeholder="Price (cents)"
            />
            <Input
              type="number"
              min={1}
              value={createForm.duration_minutes}
              onChange={(event) => setCreateForm((prev) => ({ ...prev, duration_minutes: event.target.value }))}
              placeholder="Duration (minutes)"
            />
            <Button type="button" disabled={isSaving} onClick={() => void createService()}>
              Create
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Services list</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search services"
          />

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          ) : null}

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Name</th>
                  <th className="px-4 py-3 font-semibold">Duration</th>
                  <th className="px-4 py-3 font-semibold">Price</th>
                  <th className="px-4 py-3 font-semibold">Active</th>
                  <th className="px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={5}>
                      Loading services...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={5}>
                      No services found.
                    </td>
                  </tr>
                ) : (
                  items.map((service) => (
                    <tr key={service.id}>
                      <td className="px-4 py-3 font-semibold text-slate-900">{service.name}</td>
                      <td className="px-4 py-3 text-slate-600">{service.duration_minutes} min</td>
                      <td className="px-4 py-3 text-slate-600">${(service.price_cents / 100).toFixed(2)}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            service.is_active ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                          }`}
                        >
                          {service.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button type="button" variant="secondary" onClick={() => beginEdit(service)}>
                            Edit
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            disabled={isSaving}
                            onClick={() => void toggleActive(service)}
                          >
                            {service.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">{total} service(s)</p>
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
            <CardTitle>Edit service</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <Input
                value={editForm.name}
                onChange={(event) => setEditForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Service name"
              />
              <Input
                type="number"
                min={0}
                value={editForm.price_cents}
                onChange={(event) => setEditForm((prev) => ({ ...prev, price_cents: event.target.value }))}
                placeholder="Price (cents)"
              />
              <Input
                type="number"
                min={1}
                value={editForm.duration_minutes}
                onChange={(event) => setEditForm((prev) => ({ ...prev, duration_minutes: event.target.value }))}
                placeholder="Duration (minutes)"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" disabled={isSaving} onClick={() => void saveEdit()}>
                Save changes
              </Button>
              <Button type="button" variant="secondary" onClick={() => setEditing(null)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
