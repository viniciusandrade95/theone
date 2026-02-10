"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type {
  AnalyticsAtRisk,
  AnalyticsBookingsOverTime,
  AnalyticsHeatmap,
  AnalyticsOverview,
  AnalyticsServicesBreakdown,
} from "@/lib/contracts/analytics";
import { useDefaultLocation } from "@/lib/default-location";
import { appPath } from "@/lib/paths";

const WEEKDAYS: Array<"mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun"> = [
  "mon",
  "tue",
  "wed",
  "thu",
  "fri",
  "sat",
  "sun",
];

function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function toRangeIso(fromDate: string, toDate: string): { from: string; to: string } | null {
  if (!fromDate || !toDate) {
    return null;
  }
  const from = new Date(`${fromDate}T00:00:00Z`);
  const toExclusive = new Date(`${toDate}T00:00:00Z`);
  toExclusive.setUTCDate(toExclusive.getUTCDate() + 1);
  if (Number.isNaN(from.getTime()) || Number.isNaN(toExclusive.getTime()) || from >= toExclusive) {
    return null;
  }
  return { from: from.toISOString(), to: toExclusive.toISOString() };
}

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string; error?: string } } })?.response;
  return response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }
  return parsed.toLocaleString();
}

function weekdayLabel(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function cellColor(count: number, max: number): string {
  if (count <= 0 || max <= 0) {
    return "rgba(148, 163, 184, 0.08)";
  }
  const alpha = 0.18 + (count / max) * 0.72;
  return `rgba(15, 23, 42, ${alpha.toFixed(3)})`;
}

export default function AnalyticsPage() {
  const { defaultLocation, isLoading: isLoadingDefaultLocation } = useDefaultLocation();
  const [thresholdDays, setThresholdDays] = useState(45);

  const [draftFromDate, setDraftFromDate] = useState(() => {
    const start = new Date();
    start.setUTCDate(start.getUTCDate() - 29);
    return isoDate(start);
  });
  const [draftToDate, setDraftToDate] = useState(() => isoDate(new Date()));

  const [activeFromDate, setActiveFromDate] = useState(draftFromDate);
  const [activeToDate, setActiveToDate] = useState(draftToDate);

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [services, setServices] = useState<AnalyticsServicesBreakdown | null>(null);
  const [heatmap, setHeatmap] = useState<AnalyticsHeatmap | null>(null);
  const [bookingsOverTime, setBookingsOverTime] = useState<AnalyticsBookingsOverTime | null>(null);
  const [atRisk, setAtRisk] = useState<AnalyticsAtRisk | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rangeIso = useMemo(() => toRangeIso(activeFromDate, activeToDate), [activeFromDate, activeToDate]);
  const hasDraftChanges = draftFromDate !== activeFromDate || draftToDate !== activeToDate;

  useEffect(() => {
    let active = true;

    async function loadAnalytics() {
      if (isLoadingDefaultLocation) {
        return;
      }
      if (!rangeIso) {
        if (active) {
          setError("Please choose a valid date range.");
          setOverview(null);
          setServices(null);
          setHeatmap(null);
          setBookingsOverTime(null);
          setAtRisk(null);
        }
        return;
      }

      setIsLoading(true);
      setError(null);

      const params = {
        from: rangeIso.from,
        to: rangeIso.to,
        location_id: defaultLocation?.id ?? undefined,
      };

      try {
        const [overviewResponse, servicesResponse, heatmapResponse, trendResponse, atRiskResponse] = await Promise.all([
          api.get<AnalyticsOverview>("/analytics/overview", { params }),
          api.get<AnalyticsServicesBreakdown>("/analytics/services", { params }),
          api.get<AnalyticsHeatmap>("/analytics/heatmap", { params }),
          api.get<AnalyticsBookingsOverTime>("/analytics/bookings_over_time", { params }),
          api.get<AnalyticsAtRisk>("/analytics/at_risk", {
            params: { ...params, threshold_days: thresholdDays },
          }),
        ]);

        if (!active) {
          return;
        }

        setOverview(overviewResponse.data);
        setServices(servicesResponse.data);
        setHeatmap(heatmapResponse.data);
        setBookingsOverTime(trendResponse.data);
        setAtRisk(atRiskResponse.data);
      } catch (requestError) {
        if (active) {
          setError(toErrorMessage(requestError, "Unable to load analytics."));
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadAnalytics();
    return () => {
      active = false;
    };
  }, [rangeIso, thresholdDays, defaultLocation?.id, isLoadingDefaultLocation]);

  const heatmapByKey = useMemo(() => {
    if (!heatmap?.items) {
      return new Map<string, number>();
    }
    return new Map(heatmap.items.map((item) => [`${item.weekday}-${item.hour}`, item.count]));
  }, [heatmap]);

  const maxHeatmapCount = useMemo(() => {
    if (!heatmap?.items || heatmap.items.length === 0) {
      return 0;
    }
    return Math.max(...heatmap.items.map((item) => item.count), 0);
  }, [heatmap]);

  const maxTrendCount = useMemo(() => {
    if (!bookingsOverTime?.items || bookingsOverTime.items.length === 0) {
      return 0;
    }
    return Math.max(...bookingsOverTime.items.map((item) => item.count), 0);
  }, [bookingsOverTime]);

  const maxTopServiceCount = useMemo(() => {
    if (!services?.top_services || services.top_services.length === 0) {
      return 0;
    }
    return Math.max(...services.top_services.map((item) => item.bookings), 0);
  }, [services]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Analytics</CardTitle>
          <CardDescription>Customer behavior and booking performance across the selected range.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-sm font-medium text-slate-700">
              From
              <Input type="date" value={draftFromDate} onChange={(event) => setDraftFromDate(event.target.value)} />
            </label>
            <label className="space-y-1 text-sm font-medium text-slate-700">
              To
              <Input type="date" value={draftToDate} onChange={(event) => setDraftToDate(event.target.value)} />
            </label>
            <Button
              type="button"
              onClick={() => {
                setActiveFromDate(draftFromDate);
                setActiveToDate(draftToDate);
              }}
              disabled={!hasDraftChanges}
            >
              Apply range
            </Button>
          </div>
        </CardContent>
      </Card>

      {error ? <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">Loading analytics...</p> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Card>
          <CardHeader>
            <CardTitle>Total appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-slate-900">{overview?.total_appointments_created ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-emerald-700">{overview?.completed_count ?? 0}</p>
            <p className="text-xs text-slate-500">{formatPercent(overview?.completion_rate ?? 0)} rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Cancelled</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-rose-700">{overview?.cancelled_count ?? 0}</p>
            <p className="text-xs text-slate-500">{formatPercent(overview?.cancellation_rate ?? 0)} rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>No-show</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-amber-700">{overview?.no_show_count ?? 0}</p>
            <p className="text-xs text-slate-500">{formatPercent(overview?.no_show_rate ?? 0)} rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Repeat customers</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-slate-900">{overview?.returning_customers ?? 0}</p>
            <p className="text-xs text-slate-500">{formatPercent(overview?.repeat_rate ?? 0)} repeat rate</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Bookings Over Time</CardTitle>
            <CardDescription>Daily booking count for the selected period.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-80 space-y-2 overflow-auto pr-1">
              {(bookingsOverTime?.items ?? []).map((point) => {
                const widthPct = maxTrendCount > 0 ? (point.count / maxTrendCount) * 100 : 0;
                return (
                  <div key={point.date} className="space-y-1">
                    <div className="flex items-center justify-between text-xs text-slate-600">
                      <span>{point.date}</span>
                      <span>{point.count}</span>
                    </div>
                    <div className="h-2 rounded bg-slate-100">
                      <div className="h-2 rounded bg-slate-900" style={{ width: `${widthPct}%` }} />
                    </div>
                  </div>
                );
              })}
              {(bookingsOverTime?.items?.length ?? 0) === 0 ? (
                <p className="text-sm text-slate-500">No bookings in this range.</p>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status Breakdown</CardTitle>
            <CardDescription>Appointment lifecycle distribution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="h-4 w-full overflow-hidden rounded bg-slate-100">
              {(() => {
                const total =
                  (overview?.status_breakdown.booked ?? 0) +
                  (overview?.status_breakdown.completed ?? 0) +
                  (overview?.status_breakdown.cancelled ?? 0) +
                  (overview?.status_breakdown.no_show ?? 0);
                const bookedWidth = total > 0 ? ((overview?.status_breakdown.booked ?? 0) / total) * 100 : 0;
                const completedWidth = total > 0 ? ((overview?.status_breakdown.completed ?? 0) / total) * 100 : 0;
                const cancelledWidth = total > 0 ? ((overview?.status_breakdown.cancelled ?? 0) / total) * 100 : 0;
                const noShowWidth = total > 0 ? ((overview?.status_breakdown.no_show ?? 0) / total) * 100 : 0;
                return (
                  <div className="flex h-full w-full">
                    <div className="h-full bg-blue-500" style={{ width: `${bookedWidth}%` }} />
                    <div className="h-full bg-emerald-500" style={{ width: `${completedWidth}%` }} />
                    <div className="h-full bg-rose-500" style={{ width: `${cancelledWidth}%` }} />
                    <div className="h-full bg-amber-500" style={{ width: `${noShowWidth}%` }} />
                  </div>
                );
              })()}
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm text-slate-700">
              <p>Booked: {overview?.status_breakdown.booked ?? 0}</p>
              <p>Completed: {overview?.status_breakdown.completed ?? 0}</p>
              <p>Cancelled: {overview?.status_breakdown.cancelled ?? 0}</p>
              <p>No-show: {overview?.status_breakdown.no_show ?? 0}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm text-slate-700">
              <p>New customers: {overview?.new_customers ?? 0}</p>
              <p>Returning customers: {overview?.returning_customers ?? 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Services</CardTitle>
            <CardDescription>Most booked services and mix distribution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(services?.top_services ?? []).map((item) => {
              const widthPct = maxTopServiceCount > 0 ? (item.bookings / maxTopServiceCount) * 100 : 0;
              return (
                <div key={`${item.service_id ?? "none"}-${item.service_name}`} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-slate-700">
                    <span>{item.service_name}</span>
                    <span>
                      {item.bookings} ({formatPercent(item.share)})
                    </span>
                  </div>
                  <div className="h-2 rounded bg-slate-100">
                    <div className="h-2 rounded bg-slate-900" style={{ width: `${widthPct}%` }} />
                  </div>
                </div>
              );
            })}
            {(services?.top_services?.length ?? 0) === 0 ? (
              <p className="text-sm text-slate-500">No services booked in this range.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bookings Heatmap</CardTitle>
            <CardDescription>
              Weekday and hour distribution ({heatmap?.timezone ?? "UTC"}).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <div className="min-w-[980px] space-y-2">
                <div className="grid grid-cols-[56px_repeat(24,minmax(0,1fr))] gap-1 text-[10px] text-slate-500">
                  <div />
                  {Array.from({ length: 24 }).map((_, hour) => (
                    <div key={`hour-${hour}`} className="text-center">
                      {hour}
                    </div>
                  ))}
                </div>
                {WEEKDAYS.map((weekday) => (
                  <div key={weekday} className="grid grid-cols-[56px_repeat(24,minmax(0,1fr))] gap-1">
                    <div className="pr-1 text-right text-xs font-semibold text-slate-600">{weekdayLabel(weekday)}</div>
                    {Array.from({ length: 24 }).map((_, hour) => {
                      const count = heatmapByKey.get(`${weekday}-${hour}`) ?? 0;
                      return (
                        <div
                          key={`${weekday}-${hour}`}
                          className="h-5 rounded"
                          title={`${weekdayLabel(weekday)} ${hour}:00 - ${count} bookings`}
                          style={{ backgroundColor: cellColor(count, maxHeatmapCount) }}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>At-Risk Customers</CardTitle>
            <CardDescription>No appointments in the configured threshold window.</CardDescription>
          </div>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Threshold
            <select
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900"
              value={thresholdDays}
              onChange={(event) => setThresholdDays(Number(event.target.value))}
            >
              <option value={45}>45 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </label>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Customer</th>
                  <th className="px-2 py-2">Phone</th>
                  <th className="px-2 py-2">Email</th>
                  <th className="px-2 py-2">Last appointment</th>
                  <th className="px-2 py-2">Days since</th>
                </tr>
              </thead>
              <tbody>
                {(atRisk?.items ?? []).map((item) => (
                  <tr key={item.customer_id} className="border-b border-slate-100 text-slate-700">
                    <td className="px-2 py-2 font-medium">
                      <Link href={appPath(`/dashboard/customers/${item.customer_id}`)} className="hover:underline">
                        {item.customer_name}
                      </Link>
                    </td>
                    <td className="px-2 py-2">{item.customer_phone || "-"}</td>
                    <td className="px-2 py-2">{item.customer_email || "-"}</td>
                    <td className="px-2 py-2">{formatDateTime(item.last_appointment_at)}</td>
                    <td className="px-2 py-2">{item.days_since_last_appointment}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(atRisk?.items?.length ?? 0) === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No at-risk customers for the selected threshold.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
