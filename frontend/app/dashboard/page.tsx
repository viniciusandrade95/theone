"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendMiniCard } from "@/components/dashboard/TrendMiniCard";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";
import type { DashboardAppointmentItem, DashboardOverview, InactiveCustomerItem } from "@/lib/contracts/dashboard";
import type { OutboundMessage, Paginated } from "@/lib/contracts/outbound";

function toErrorMessage(error: unknown): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return (
    response?.data?.details?.message ??
    response?.data?.message ??
    response?.data?.detail ??
    response?.data?.error ??
    "Failed to load dashboard."
  );
}

function formatInTz(dtIso: string, tz: string, options: Intl.DateTimeFormatOptions) {
  try {
    return new Intl.DateTimeFormat(undefined, { timeZone: tz, ...options }).format(new Date(dtIso));
  } catch {
    return new Intl.DateTimeFormat(undefined, options).format(new Date(dtIso));
  }
}

function appointmentHref(appointmentId: string) {
  const encoded = encodeURIComponent(appointmentId);
  return appPath(`/dashboard/appointments?appointment_id=${encoded}#appointment-${encoded}`);
}

const secondaryLinkClass =
  "inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition hover:border-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2";

function StatCard({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold text-slate-900">{value}</p>
        {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

function AppointmentRow({ item, tz, badge }: { item: DashboardAppointmentItem; tz: string; badge?: string }) {
  const time = `${formatInTz(item.starts_at, tz, { hour: "2-digit", minute: "2-digit" })}–${formatInTz(item.ends_at, tz, {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
  const meta = [item.service_name, item.location_name].filter(Boolean).join(" • ");

  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 p-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <Link href={appointmentHref(item.id)} className="text-sm font-semibold text-slate-900 hover:underline">
            {time}
          </Link>
          {badge ? (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">{badge}</span>
          ) : null}
        </div>
        <div className="mt-1 truncate text-sm text-slate-700">
          <Link href={appPath(`/dashboard/customers/${encodeURIComponent(item.customer_id)}`)} className="hover:underline">
            {item.customer_name}
          </Link>
        </div>
        {meta ? <div className="mt-1 truncate text-xs text-slate-500">{meta}</div> : null}
      </div>
      <div className="shrink-0 text-right text-xs text-slate-500">
        <div>{formatInTz(item.starts_at, tz, { weekday: "short", month: "short", day: "2-digit" })}</div>
      </div>
    </div>
  );
}

function InactiveCustomerRow({ item }: { item: InactiveCustomerItem }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 p-3">
      <div className="min-w-0">
        <Link
          href={appPath(`/dashboard/customers/${encodeURIComponent(item.id)}`)}
          className="text-sm font-semibold text-slate-900 hover:underline"
        >
          {item.name}
        </Link>
        <div className="mt-1 truncate text-xs text-slate-500">
          {[item.phone, item.email].filter(Boolean).join(" • ") || "No contact info"}
        </div>
      </div>
      <div className="shrink-0 text-right text-xs text-slate-500">
        <div>{item.last_completed_at ? "Last visit:" : "Last visit:"}</div>
        <div className="font-semibold text-slate-700">{item.last_completed_at ? new Date(item.last_completed_at).toLocaleDateString() : "Never"}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [recentOutbound, setRecentOutbound] = useState<OutboundMessage[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setLoadError(null);
    void Promise.all([
      api.get<DashboardOverview>("/crm/dashboard/overview"),
      api
        .get<Paginated<OutboundMessage>>("/crm/outbound/messages", { params: { page: 1, page_size: 25 } })
        .catch(() => ({ data: { items: [] } } as any)),
    ])
      .then(([overviewResponse, outboundResponse]) => {
        if (!mounted) return;
        setOverview(overviewResponse.data);
        setRecentOutbound(outboundResponse.data?.items ?? []);
      })
      .catch((err) => {
        if (!mounted) return;
        setLoadError(toErrorMessage(err));
      })
      .finally(() => {
        if (!mounted) return;
        setIsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const tz = overview?.timezone ?? "UTC";

  const opportunityCards = useMemo(() => {
    const counts = overview?.counts;
    return [
      {
        title: "Confirm bookings",
        value: counts?.appointments_pending_confirmation_count ?? 0,
        description: "Appointments awaiting confirmation.",
        href: appPath("/dashboard/appointments"),
        pill:
          (counts?.appointments_pending_confirmation_count ?? 0) > 0
            ? ({ label: "Action", tone: "warning" } as const)
            : ({ label: "Clear", tone: "neutral" } as const),
      },
      {
        title: "Win back customers",
        value: counts?.inactive_customers_count ?? 0,
        description: "No completed visit in 60 days.",
        href: appPath("/dashboard/customers"),
        pill:
          (counts?.inactive_customers_count ?? 0) > 0
            ? ({ label: "Opportunity", tone: "positive" } as const)
            : ({ label: "Clear", tone: "neutral" } as const),
      },
      {
        title: "No-show watch",
        value: counts?.recent_no_shows_count ?? 0,
        description: "No-shows in the last 14 days.",
        href: appPath("/dashboard/appointments"),
        pill:
          (counts?.recent_no_shows_count ?? 0) > 0
            ? ({ label: "Review", tone: "warning" } as const)
            : ({ label: "Clear", tone: "neutral" } as const),
      },
      {
        title: "Online bookings",
        value: counts?.new_online_bookings_count ?? 0,
        description: "Created online today (proxy).",
        href: appPath("/dashboard/appointments"),
        pill:
          (counts?.new_online_bookings_count ?? 0) > 0
            ? ({ label: "New", tone: "positive" } as const)
            : ({ label: "None", tone: "neutral" } as const),
      },
    ];
  }, [overview?.counts]);

  const quickActions = useMemo(
    () => [
      { label: "Create customer", href: "/dashboard/customers/new" },
      { label: "Create appointment", href: "/dashboard/appointments" },
      { label: "Send message", href: "/dashboard/customers" },
      { label: "Enable booking online", href: "/dashboard/settings/booking" },
      { label: "Import customers", href: "/dashboard/customers/import" },
    ],
    [],
  );

  const deliverySnapshot = useMemo(() => {
    const counts = { queued: 0, sent: 0, delivered: 0, read: 0, failed: 0, manual: 0 };
    let latestUpdate: string | null = null;
    let total = 0;

    for (const message of recentOutbound) {
      if ((message.channel || "").toLowerCase() !== "whatsapp") continue;
      total += 1;

      const rawState = ((message as any).delivery_state ?? message.delivery_status ?? "").toString().trim().toLowerCase();
      const deliveryState =
        rawState === "queued" || rawState === "accepted" || rawState === "sent" || rawState === "delivered" || rawState === "read" || rawState === "failed" || rawState === "unconfirmed"
          ? rawState
          : message.status === "failed"
            ? "failed"
            : message.status === "sent"
              ? "unconfirmed"
              : null;

      if (deliveryState === "queued") counts.queued += 1;
      else if (deliveryState === "accepted" || deliveryState === "sent") counts.sent += 1;
      else if (deliveryState === "delivered") counts.delivered += 1;
      else if (deliveryState === "read") counts.read += 1;
      else if (deliveryState === "failed") counts.failed += 1;
      else if (deliveryState === "unconfirmed") counts.manual += 1;

      const candidate = message.delivery_status_updated_at || message.created_at;
      if (!latestUpdate || new Date(candidate).getTime() > new Date(latestUpdate).getTime()) {
        latestUpdate = candidate;
      }
    }

    return { counts, latestUpdate, total };
  }, [recentOutbound]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Overview</h1>
          <p className="text-sm text-slate-500">Today’s operational snapshot. Times shown in {tz}.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button type="button" variant="secondary" onClick={() => window.location.reload()} disabled={isLoading}>
            Refresh
          </Button>
        </div>
      </div>

      {loadError ? (
        <Card>
          <CardContent className="py-4 text-sm text-rose-700">{loadError}</CardContent>
        </Card>
      ) : null}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        <StatCard label="Appointments today" value={overview?.counts.appointments_today_count ?? 0} />
        <StatCard label="Pending confirmation" value={overview?.counts.appointments_pending_confirmation_count ?? 0} />
        <StatCard label="Tasks today" value={overview?.counts.tasks_today_count ?? 0} hint="Not available yet" />
        <StatCard label="Inactive customers" value={overview?.counts.inactive_customers_count ?? 0} />
        <StatCard label="Scheduled reminders" value={overview?.counts.scheduled_reminders_count ?? 0} hint="Not available yet" />
        <StatCard label="Recent no-shows" value={overview?.counts.recent_no_shows_count ?? 0} hint="Last 14 days" />
        <StatCard label="New online bookings today" value={overview?.counts.new_online_bookings_count ?? 0} hint="Proxy-based" />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {opportunityCards.map((card) => (
          <TrendMiniCard
            key={card.title}
            title={card.title}
            value={card.value}
            description={card.description}
            href={card.href}
            pill={card.pill}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>WhatsApp delivery</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
              Sending {deliverySnapshot.counts.queued}
            </span>
            <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
              Sent {deliverySnapshot.counts.sent}
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              Delivered {deliverySnapshot.counts.delivered}
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              Read {deliverySnapshot.counts.read}
            </span>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
              Manual {deliverySnapshot.counts.manual}
            </span>
            <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700">
              Failed {deliverySnapshot.counts.failed}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Provider sends are trackable. Manual sends can’t be confirmed (they show as Manual). Last update:{" "}
            <span className="font-semibold text-slate-700">
              {deliverySnapshot.latestUpdate ? new Date(deliverySnapshot.latestUpdate).toLocaleString() : "—"}
            </span>
            {deliverySnapshot.total > 0 ? <span className="text-slate-400"> • last {deliverySnapshot.total} messages</span> : null}
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href={appPath("/dashboard/customers")} className={secondaryLinkClass}>
              View customers
            </Link>
            <Link href={appPath("/dashboard/outbound/templates")} className={secondaryLinkClass}>
              Manage templates
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick actions</CardTitle>
        </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
          {quickActions.map((action) => (
            <Link key={action.href} href={appPath(action.href)} className={secondaryLinkClass}>
              {action.label}
            </Link>
          ))}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Appointments today</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(overview?.sections.appointments_today ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No appointments to handle today.</p>
            ) : (
              overview?.sections.appointments_today.map((item) => <AppointmentRow key={item.id} item={item} tz={tz} />)
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Appointments pending confirmation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(overview?.sections.appointments_pending_confirmation ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No appointments pending confirmation.</p>
            ) : (
              overview?.sections.appointments_pending_confirmation.map((item) => (
                <AppointmentRow key={item.id} item={item} tz={tz} badge="Needs confirmation" />
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inactive customers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(overview?.sections.inactive_customers ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No inactive customers found.</p>
            ) : (
              overview?.sections.inactive_customers.map((item) => <InactiveCustomerRow key={item.id} item={item} />)
            )}
            <p className="pt-2 text-xs text-slate-500">Inactive = no completed appointment in the last 60 days.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>New online bookings today</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(overview?.sections.new_online_bookings ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No new online bookings today.</p>
            ) : (
              overview?.sections.new_online_bookings.map((item) => (
                <AppointmentRow key={item.id} item={item} tz={tz} badge="Online booking (proxy)" />
              ))
            )}
            <p className="pt-2 text-xs text-slate-500">
              Uses proxy: created_by_user_id is empty and created_at is within today window.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent no-shows</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(overview?.sections.recent_no_shows ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No recent no-shows.</p>
            ) : (
              overview?.sections.recent_no_shows.map((item) => <AppointmentRow key={item.id} item={item} tz={tz} badge="No-show" />)
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tasks & reminders</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-500">
            <p>Tasks and scheduled reminders are not implemented yet in this MVP.</p>
            {overview?.notes?.length ? (
              <ul className="list-disc space-y-1 pl-5 text-xs">
                {overview.notes.slice(0, 3).map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
