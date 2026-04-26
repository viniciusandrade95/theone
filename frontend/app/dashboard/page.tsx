"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
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

function sortAppointments(items: DashboardAppointmentItem[]) {
  return [...items].sort((a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime());
}

function AppointmentRow({ item, tz, badge }: { item: DashboardAppointmentItem; tz: string; badge?: string }) {
  const time = `${formatInTz(item.starts_at, tz, { hour: "2-digit", minute: "2-digit" })}–${formatInTz(item.ends_at, tz, {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
  const meta = [item.service_name, item.location_name].filter(Boolean).join(" • ");

  return (
    <div className="rounded-2xl border border-[var(--ds-line)] bg-[var(--ds-surface)] p-3 shadow-[var(--mb-shadow-xs)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Link href={appointmentHref(item.id)} className="text-sm font-extrabold text-[var(--ds-text)] hover:underline">
              {time}
            </Link>
            {badge ? <span className="ds-chip ds-chip-accent">{badge}</span> : null}
          </div>
          <Link
            href={appPath(`/dashboard/customers/${encodeURIComponent(item.customer_id)}`)}
            className="mt-1 block truncate text-sm font-semibold text-[var(--ds-text)] hover:underline"
          >
            {item.customer_name}
          </Link>
          {meta ? <div className="mt-1 truncate text-xs text-[var(--ds-muted)]">{meta}</div> : null}
        </div>
        <div className="shrink-0 text-right text-xs font-semibold text-[var(--ds-muted)]">
          {formatInTz(item.starts_at, tz, { weekday: "short", month: "short", day: "2-digit" })}
        </div>
      </div>
    </div>
  );
}

function InactiveCustomerRow({ item }: { item: InactiveCustomerItem }) {
  return (
    <div className="rounded-2xl border border-[var(--ds-line)] bg-[var(--ds-surface)] p-3 shadow-[var(--mb-shadow-xs)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href={appPath(`/dashboard/customers/${encodeURIComponent(item.id)}`)}
            className="text-sm font-extrabold text-[var(--ds-text)] hover:underline"
          >
            {item.name}
          </Link>
          <div className="mt-1 truncate text-xs text-[var(--ds-muted)]">
            {[item.phone, item.email].filter(Boolean).join(" • ") || "No contact info"}
          </div>
        </div>
        <div className="shrink-0 text-right text-xs text-[var(--ds-muted)]">
          <div>Last visit</div>
          <div className="font-extrabold text-[var(--ds-text)]">{item.last_completed_at ? new Date(item.last_completed_at).toLocaleDateString() : "Never"}</div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, hint, tone = "default" }: { label: string; value: string | number; hint?: string; tone?: "default" | "primary" }) {
  return (
    <article className={`ds-metric-card ${tone === "primary" ? "bg-[var(--ds-primary-soft)]" : ""}`}>
      <span className="ds-metric-label">{label}</span>
      <strong className="ds-metric-value">{value}</strong>
      {hint ? <span className="ds-metric-trend text-[var(--ds-muted)]">{hint}</span> : null}
    </article>
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
  const counts = overview?.counts;

  const todayAppointments = useMemo(() => sortAppointments(overview?.sections.appointments_today ?? []), [overview?.sections.appointments_today]);
  const pendingAppointments = overview?.sections.appointments_pending_confirmation ?? [];
  const newOnlineBookings = overview?.sections.new_online_bookings ?? [];
  const inactiveCustomers = overview?.sections.inactive_customers ?? [];
  const recentNoShows = overview?.sections.recent_no_shows ?? [];

  const nextAppointment = useMemo(() => {
    const now = Date.now();
    return todayAppointments.find((item) => new Date(item.ends_at).getTime() >= now) ?? todayAppointments[0] ?? null;
  }, [todayAppointments]);

  const lastAppointment = todayAppointments.length ? todayAppointments[todayAppointments.length - 1] : null;

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

  const actionCount =
    (counts?.appointments_pending_confirmation_count ?? 0) +
    (counts?.new_online_bookings_count ?? 0) +
    deliverySnapshot.counts.failed;

  const attentionLabel = [
    (counts?.appointments_pending_confirmation_count ?? 0) > 0 ? `${counts?.appointments_pending_confirmation_count} bookings to confirm` : null,
    (counts?.new_online_bookings_count ?? 0) > 0 ? `${counts?.new_online_bookings_count} new online bookings` : null,
    deliverySnapshot.counts.failed > 0 ? `${deliverySnapshot.counts.failed} failed WhatsApp sends` : null,
  ]
    .filter(Boolean)
    .join(" • ");

  const currentDateLabel = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "2-digit" }).format(new Date());
  const nextStartTime = nextAppointment ? formatInTz(nextAppointment.starts_at, tz, { hour: "2-digit", minute: "2-digit" }) : "—";
  const nextEndTime = nextAppointment ? formatInTz(nextAppointment.ends_at, tz, { hour: "2-digit", minute: "2-digit" }) : null;
  const dayEndTime = lastAppointment ? formatInTz(lastAppointment.ends_at, tz, { hour: "2-digit", minute: "2-digit" }) : "—";

  return (
    <div className="ds-premium-bg -m-4 min-h-screen p-4 md:-m-6 md:p-6 xl:rounded-[2rem]">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="ds-card relative overflow-hidden p-5">
          <div className="pointer-events-none absolute -right-8 -top-8 h-36 w-36 rounded-full bg-[var(--ds-primary-soft)] blur-2xl" />
          <div className="pointer-events-none absolute -left-10 bottom-0 h-28 w-28 rounded-full bg-[var(--ds-aqua-soft)] blur-2xl" />
          <div className="relative flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="max-w-2xl">
              <div className="mb-3 inline-flex rounded-full border border-[var(--ds-line)] bg-[var(--ds-surface-glass)] px-3 py-1 text-xs font-extrabold text-[var(--ds-muted)]">
                {currentDateLabel} · {actionCount > 0 ? `${actionCount} actions pending` : "all clear"}
              </div>
              <h1 className="text-3xl font-black tracking-[-0.04em] text-[var(--ds-text)] md:text-4xl">Good morning, João</h1>
              <p className="mt-2 text-sm font-medium text-[var(--ds-muted)]">
                Your day, bookings, customer attention and next actions in one calm place. Times shown in {tz}.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button type="button" variant="secondary" onClick={() => window.location.reload()} disabled={isLoading}>
                {isLoading ? "Refreshing…" : "Refresh"}
              </Button>
            </div>
          </div>
        </header>

        {loadError ? <div className="ds-attention-strip border-rose-200 bg-[var(--ds-danger-soft)] text-[var(--ds-danger)]">{loadError}</div> : null}

        <label className="ds-search max-w-2xl">
          <span className="text-lg text-[var(--ds-muted)]">⌕</span>
          <input placeholder="Search customers, appointments or services…" />
        </label>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(22rem,0.75fr)]">
          <main className="space-y-5">
            <section className="ds-card p-4 md:p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="ds-metric-label">Live agenda</span>
                  <h2 className="mt-1 text-2xl font-black tracking-[-0.04em] text-[var(--ds-text)]">{nextAppointment ? "Next appointment" : "No appointments left today"}</h2>
                </div>
                <Link href={appPath("/dashboard/calendar")} className="ds-button ds-button-secondary min-h-9 px-3 text-xs">
                  Open agenda
                </Link>
              </div>

              <div className="mt-4 rounded-3xl border border-[var(--ds-line)] bg-[var(--ds-surface)] p-4 shadow-[var(--mb-shadow-xs)]">
                <div className="grid gap-4 md:grid-cols-[7rem_1fr] md:items-center">
                  <div className="text-4xl font-black tracking-[-0.05em] text-[var(--ds-primary-strong)]">{nextStartTime}</div>
                  <div className="min-w-0">
                    <div className="text-lg font-black text-[var(--ds-text)]">{nextAppointment?.customer_name ?? "Use the calendar to plan the next slot"}</div>
                    <div className="mt-1 text-sm text-[var(--ds-muted)]">
                      {nextAppointment
                        ? `${[nextAppointment.service_name, nextAppointment.location_name].filter(Boolean).join(" • ") || "Appointment"}${nextEndTime ? ` · ends ${nextEndTime}` : ""}`
                        : "Create a booking or block time for focus."}
                    </div>
                  </div>
                </div>
                <div className="mt-4 grid gap-2 sm:grid-cols-3">
                  <span className="ds-chip">Today: {counts?.appointments_today_count ?? 0}</span>
                  <span className="ds-chip ds-chip-accent">Day ends {dayEndTime}</span>
                  <span className="ds-chip">Confirmations: {counts?.appointments_pending_confirmation_count ?? 0}</span>
                </div>
              </div>
            </section>

            <section className="ds-attention-strip">
              <div>
                <span className="ds-attention-title">
                  {actionCount > 0 ? `${actionCount} actions need your attention` : "No urgent actions right now"}
                </span>
                <span className="ds-attention-subtitle">
                  {attentionLabel || "No pending confirmations, online bookings or failed WhatsApp sends."}
                </span>
              </div>
              <Link href={appPath("/dashboard/appointments")} className="ds-button ds-button-primary min-h-9 px-3 text-xs">
                Resolve
              </Link>
            </section>

            <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Link href={appPath("/dashboard/appointments")} className="ds-card-soft p-4 text-center text-sm font-black text-[var(--ds-text)] hover:shadow-[var(--mb-shadow-sm)]">
                <span className="block text-xl text-[var(--ds-primary-strong)]">＋</span>
                Book
              </Link>
              <Link href={appPath("/dashboard/customers/new")} className="ds-card-soft bg-[var(--ds-accent-soft)] p-4 text-center text-sm font-black text-[var(--ds-text)] hover:shadow-[var(--mb-shadow-sm)]">
                <span className="block text-xl text-[var(--ds-primary-strong)]">☺</span>
                Client
              </Link>
              <Link href={appPath("/dashboard/customers")} className="ds-card-soft p-4 text-center text-sm font-black text-[var(--ds-text)] hover:shadow-[var(--mb-shadow-sm)]">
                <span className="block text-xl text-[var(--ds-primary-strong)]">✉</span>
                Message
              </Link>
              <Link href={appPath("/dashboard/settings/booking")} className="ds-card-soft bg-[var(--ds-aqua-soft)] p-4 text-center text-sm font-black text-[var(--ds-text)] hover:shadow-[var(--mb-shadow-sm)]">
                <span className="block text-xl text-[var(--ds-primary-strong)]">↗</span>
                Booking link
              </Link>
            </section>

            <section className="grid gap-3 md:grid-cols-4">
              <MetricCard label="Appointments today" value={counts?.appointments_today_count ?? 0} hint="From today's calendar" tone="primary" />
              <MetricCard label="Pending confirmation" value={counts?.appointments_pending_confirmation_count ?? 0} hint="Needs action" />
              <MetricCard label="New online bookings" value={counts?.new_online_bookings_count ?? 0} hint="Created today" />
              <MetricCard label="Revenue today" value="—" hint="Finance source not connected yet" />
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="ds-card p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h2 className="text-lg font-black text-[var(--ds-text)]">Today's appointments</h2>
                  <Link href={appPath("/dashboard/calendar")} className="text-xs font-extrabold text-[var(--ds-primary-strong)]">
                    Calendar
                  </Link>
                </div>
                <div className="space-y-2">
                  {todayAppointments.length === 0 ? (
                    <p className="text-sm text-[var(--ds-muted)]">No appointments to handle today.</p>
                  ) : (
                    todayAppointments.slice(0, 4).map((item) => <AppointmentRow key={item.id} item={item} tz={tz} />)
                  )}
                </div>
              </div>

              <div className="ds-card p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h2 className="text-lg font-black text-[var(--ds-text)]">Needs confirmation</h2>
                  <Link href={appPath("/dashboard/appointments")} className="text-xs font-extrabold text-[var(--ds-primary-strong)]">
                    View all
                  </Link>
                </div>
                <div className="space-y-2">
                  {pendingAppointments.length === 0 ? (
                    <p className="text-sm text-[var(--ds-muted)]">No appointments pending confirmation.</p>
                  ) : (
                    pendingAppointments.slice(0, 4).map((item) => <AppointmentRow key={item.id} item={item} tz={tz} badge="Confirm" />)
                  )}
                </div>
              </div>
            </section>
          </main>

          <aside className="space-y-5">
            <section className="ds-card p-4">
              <h2 className="mb-3 text-lg font-black text-[var(--ds-text)]">WhatsApp delivery</h2>
              <div className="grid grid-cols-2 gap-2 text-xs font-extrabold">
                <span className="ds-chip">Sending {deliverySnapshot.counts.queued}</span>
                <span className="ds-chip">Sent {deliverySnapshot.counts.sent}</span>
                <span className="ds-chip ds-chip-success">Delivered {deliverySnapshot.counts.delivered}</span>
                <span className="ds-chip ds-chip-success">Read {deliverySnapshot.counts.read}</span>
                <span className="ds-chip ds-chip-accent">Manual {deliverySnapshot.counts.manual}</span>
                <span className="ds-chip ds-chip-warning">Failed {deliverySnapshot.counts.failed}</span>
              </div>
              <p className="mt-3 text-xs text-[var(--ds-muted)]">
                Last update: {deliverySnapshot.latestUpdate ? new Date(deliverySnapshot.latestUpdate).toLocaleString() : "—"}
                {deliverySnapshot.total > 0 ? ` · last ${deliverySnapshot.total} messages` : ""}
              </p>
            </section>

            <section className="ds-card p-4">
              <h2 className="mb-3 text-lg font-black text-[var(--ds-text)]">Customer opportunities</h2>
              <div className="space-y-2">
                {inactiveCustomers.length === 0 ? (
                  <p className="text-sm text-[var(--ds-muted)]">No inactive customers found.</p>
                ) : (
                  inactiveCustomers.slice(0, 4).map((item) => <InactiveCustomerRow key={item.id} item={item} />)
                )}
              </div>
              <p className="mt-3 text-xs text-[var(--ds-muted)]">Inactive = no completed appointment in the last 60 days.</p>
            </section>

            <section className="ds-card p-4">
              <h2 className="mb-3 text-lg font-black text-[var(--ds-text)]">Operational signals</h2>
              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <MetricCard label="Inactive customers" value={counts?.inactive_customers_count ?? 0} hint="Win-back candidates" />
                <MetricCard label="Recent no-shows" value={counts?.recent_no_shows_count ?? 0} hint="Last 14 days" />
                <MetricCard label="Tasks today" value={counts?.tasks_today_count ?? 0} hint="Not available yet" />
              </div>
              {recentNoShows.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {recentNoShows.slice(0, 2).map((item) => <AppointmentRow key={item.id} item={item} tz={tz} badge="No-show" />)}
                </div>
              ) : null}
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
