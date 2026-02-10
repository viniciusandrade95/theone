"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";

type Stage = "lead" | "booked" | "completed";

type Customer = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  stage: Stage;
  created_at: string;
};

type Appointment = {
  id: string;
  starts_at: string;
};

type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

const PAGE_SIZE = 25;

function toErrorMessage(error: unknown): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return (
    response?.data?.details?.message ||
    response?.data?.message ||
    response?.data?.detail ||
    response?.data?.error ||
    "Unable to load customers."
  );
}

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

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleDateString();
}

export default function CustomersPage() {
  const router = useRouter();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [nextAppointments, setNextAppointments] = useState<Record<string, string>>({});

  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [stageFilter, setStageFilter] = useState<"all" | Stage>("all");

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, stageFilter]);

  useEffect(() => {
    let active = true;

    async function run() {
      setIsLoading(true);
      setError(null);
      setNextAppointments({});

      try {
        const response = await api.get<Paginated<Customer>>("/crm/customers", {
          params: {
            page,
            page_size: PAGE_SIZE,
            query: debouncedSearch || undefined,
            stage: stageFilter === "all" ? undefined : stageFilter,
          },
        });

        if (!active) {
          return;
        }

        const items = response.data?.items ?? [];
        setCustomers(items);
        setTotal(response.data?.total ?? 0);

        if (items.length === 0) {
          return;
        }

        const now = new Date();
        const nowIso = now.toISOString();
        const oneYearAhead = new Date(now);
        oneYearAhead.setFullYear(oneYearAhead.getFullYear() + 1);
        const oneYearAheadIso = oneYearAhead.toISOString();
        const upcomingPairs = await Promise.all(
          items.map(async (customer) => {
            try {
              const upcoming = await api.get<Paginated<Appointment>>("/crm/appointments", {
                params: {
                  page: 1,
                  page_size: 1,
                  customer_id: customer.id,
                  from_dt: nowIso,
                  to_dt: oneYearAheadIso,
                  sort: "starts_at",
                  order: "asc",
                },
              });
              const next = upcoming.data?.items?.[0]?.starts_at ?? "";
              return [customer.id, next] as const;
            } catch {
              return [customer.id, ""] as const;
            }
          }),
        );

        if (!active) {
          return;
        }

        setNextAppointments(Object.fromEntries(upcomingPairs));
      } catch (requestError) {
        if (!active) {
          return;
        }
        setError(toErrorMessage(requestError));
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void run();

    return () => {
      active = false;
    };
  }, [debouncedSearch, page, stageFilter]);

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(total / PAGE_SIZE));
  }, [total]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Customers</h1>
          <p className="text-sm text-slate-500">Manage profiles, notes, and customer lifecycle.</p>
        </div>
        <Link href={appPath("/dashboard/customers/new")}>
          <Button>Create customer</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Customer list</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-[1fr_220px]">
            <Input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search by name, phone, or email"
            />
            <select
              value={stageFilter}
              onChange={(event) => setStageFilter(event.target.value as "all" | Stage)}
              className="h-11 rounded-xl border border-slate-200 px-3 text-sm text-slate-700"
            >
              <option value="all">All stages</option>
              <option value="lead">Lead</option>
              <option value="booked">Booked</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          ) : null}

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Name</th>
                  <th className="px-4 py-3 font-semibold">Phone</th>
                  <th className="px-4 py-3 font-semibold">Email</th>
                  <th className="px-4 py-3 font-semibold">Stage</th>
                  <th className="px-4 py-3 font-semibold">Created</th>
                  <th className="px-4 py-3 font-semibold">Next appointment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={6}>
                      Loading customers...
                    </td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={6}>
                      No customers found.
                    </td>
                  </tr>
                ) : (
                  customers.map((customer) => (
                    <tr
                      key={customer.id}
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() => router.push(appPath(`/dashboard/customers/${customer.id}`))}
                    >
                      <td className="px-4 py-3 font-semibold text-slate-900">{customer.name}</td>
                      <td className="px-4 py-3 text-slate-600">{customer.phone ?? "-"}</td>
                      <td className="px-4 py-3 text-slate-600">{customer.email ?? "-"}</td>
                      <td className="px-4 py-3 capitalize text-slate-700">{customer.stage}</td>
                      <td className="px-4 py-3 text-slate-600">{formatDate(customer.created_at)}</td>
                      <td className="px-4 py-3 text-slate-600">{formatDateTime(nextAppointments[customer.id])}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">{total} customer(s)</p>
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
    </div>
  );
}
