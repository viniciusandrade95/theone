"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../../components/layout/AppShell";
import { Sidebar } from "../../../components/layout/Sidebar";
import { TopBar } from "../../../components/layout/TopBar";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { api } from "../../../lib/api";

type Customer = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  tags: string[];
  stage: string;
  consent_marketing: boolean;
  created_at?: string;
};

const DEFAULT_FORM: Omit<Customer, "id" | "stage" | "created_at"> = {
  name: "",
  phone: "",
  email: "",
  tags: [],
  consent_marketing: false,
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(DEFAULT_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const submitLabel = editingId ? "Update customer" : "Add customer";
  const filteredCount = useMemo(() => customers.length, [customers]);

  const loadCustomers = async (query?: string) => {
    setIsLoading(true);
    try {
      const response = await api.get("/crm/customers", {
        params: { limit: 50, offset: 0, search: query || undefined },
      });
      setCustomers(response.data?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load customers.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editingId) {
        await api.patch(`/crm/customers/${editingId}`, {
          name: form.name,
          phone: form.phone || null,
          email: form.email || null,
          tags: form.tags,
          consent_marketing: form.consent_marketing,
        });
      } else {
        await api.post("/crm/customers", {
          name: form.name,
          phone: form.phone || null,
          email: form.email || null,
          tags: form.tags,
          consent_marketing: form.consent_marketing,
        });
      }
      setForm(DEFAULT_FORM);
      setEditingId(null);
      await loadCustomers(search);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save customer.");
    }
  };

  const handleEdit = (customer: Customer) => {
    setEditingId(customer.id);
    setForm({
      name: customer.name,
      phone: customer.phone ?? "",
      email: customer.email ?? "",
      tags: customer.tags ?? [],
      consent_marketing: customer.consent_marketing ?? false,
    });
  };

  const handleDelete = async (customerId: string) => {
    setError(null);
    try {
      await api.delete(`/crm/customers/${customerId}`);
      await loadCustomers(search);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete customer.");
    }
  };

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadCustomers(search);
  };

  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Customers</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="flex flex-col gap-3 md:flex-row md:items-center">
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name, email, or phone"
                className="md:flex-1"
              />
              <Button type="submit" variant="outline">
                Search
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setSearch("");
                  loadCustomers("");
                }}
              >
                Clear
              </Button>
            </form>
            <div className="mt-4 space-y-3">
              {isLoading ? (
                <p className="text-sm text-slate-500">Loading customers...</p>
              ) : customers.length === 0 ? (
                <p className="text-sm text-slate-500">No customers found yet.</p>
              ) : (
                customers.map((customer) => (
                  <div
                    key={customer.id}
                    className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between"
                  >
                    <div>
                      <Link
                        href={`/dashboard/customers/${customer.id}`}
                        className="text-sm font-semibold text-slate-900 hover:text-slate-700"
                      >
                        {customer.name}
                      </Link>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                        {customer.email ? <span>{customer.email}</span> : null}
                        {customer.phone ? <span>{customer.phone}</span> : null}
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">
                          {customer.stage}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" variant="outline" onClick={() => handleEdit(customer)}>
                        Edit
                      </Button>
                      <Button type="button" variant="ghost" onClick={() => handleDelete(customer.id)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
            <p className="mt-4 text-xs text-slate-500">{filteredCount} customer(s) loaded.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{editingId ? "Edit customer" : "Add new customer"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Name
                <Input
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  required
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Email
                <Input
                  value={form.email ?? ""}
                  onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                  type="email"
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Phone
                <Input
                  value={form.phone ?? ""}
                  onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Tags (comma separated)
                <Input
                  value={form.tags.join(", ")}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      tags: event.target.value
                        .split(",")
                        .map((tag) => tag.trim())
                        .filter(Boolean),
                    }))
                  }
                  placeholder="VIP, returning, ..."
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={form.consent_marketing}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, consent_marketing: event.target.checked }))
                  }
                />
                Marketing consent confirmed
              </label>
              {error ? (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                  {error}
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button type="submit" className="flex-1">
                  {submitLabel}
                </Button>
                {editingId ? (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditingId(null);
                      setForm(DEFAULT_FORM);
                    }}
                  >
                    Cancel
                  </Button>
                ) : null}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
