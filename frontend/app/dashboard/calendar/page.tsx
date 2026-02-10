"use client";

import { useEffect, useMemo, useRef, useState } from "react";

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
import type { TenantSettings } from "@/lib/contracts/settings";
import { useDefaultLocation } from "@/lib/default-location";
import { appPath } from "@/lib/paths";

type CalendarCustomer = {
  id: string;
  name: string;
  phone: string | null;
};

type CalendarService = {
  id: string;
  name: string;
  duration_min: number | null;
  price: number | null;
};

type CalendarAppointment = {
  id: string;
  starts_at: string;
  ends_at: string;
  status: AppointmentStatus;
  cancelled_reason: string | null;
  notes: string | null;
  customer: CalendarCustomer;
  service: CalendarService | null;
  location_id: string;
};

type CalendarResponse = {
  items: CalendarAppointment[];
};

type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

type CalendarTenantSettings = Pick<TenantSettings, "calendar_default_view">;

type ConflictItem = {
  id: string;
  starts_at: string;
  ends_at: string;
};

type DayLayoutEvent = {
  appointment: CalendarAppointment;
  day: string;
  startMin: number;
  endMin: number;
  col: number;
  cols: number;
  canResize: boolean;
};

type ResizeState = {
  appointmentId: string;
  day: string;
  startMin: number;
  initialEndMin: number;
  startY: number;
};

const SLOT_MINUTES = 30;
const RESIZE_SNAP_MINUTES = 15;
const MIN_EVENT_MINUTES = 15;
const TOTAL_MINUTES = 24 * 60;
const SLOT_HEIGHT_PX = 28;
const PIXELS_PER_MINUTE = SLOT_HEIGHT_PX / SLOT_MINUTES;
const GRID_HEIGHT_PX = TOTAL_MINUTES * PIXELS_PER_MINUTE;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function dayKeyFromDate(value: Date): string {
  return `${value.getFullYear()}-${pad2(value.getMonth() + 1)}-${pad2(value.getDate())}`;
}

function parseDayKey(dayKey: string): Date {
  const [year, month, day] = dayKey.split("-").map((part) => Number(part));
  if (!year || !month || !day) {
    const fallback = new Date();
    fallback.setHours(0, 0, 0, 0);
    return fallback;
  }
  return new Date(year, month - 1, day, 0, 0, 0, 0);
}

function addDays(value: Date, amount: number): Date {
  const next = new Date(value);
  next.setDate(next.getDate() + amount);
  return next;
}

function startOfWeek(value: Date): Date {
  const result = new Date(value);
  const shift = (result.getDay() + 6) % 7;
  result.setDate(result.getDate() - shift);
  result.setHours(0, 0, 0, 0);
  return result;
}

function toLocalDateTimeInput(value: Date): string {
  return `${dayKeyFromDate(value)}T${pad2(value.getHours())}:${pad2(value.getMinutes())}`;
}

function combineDayAndMinutes(day: string, minutes: number): Date {
  const base = parseDayKey(day);
  const clamped = Math.max(0, Math.min(TOTAL_MINUTES, minutes));
  base.setMinutes(clamped, 0, 0);
  return base;
}

function minutesSinceDayStart(date: Date, day: string): number {
  const dayStart = parseDayKey(day);
  return Math.round((date.getTime() - dayStart.getTime()) / 60_000);
}

function formatDayHeader(day: string): string {
  return parseDayKey(day).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function formatRangeLabel(viewMode: "week" | "day", days: string[]): string {
  if (days.length === 0) {
    return "";
  }
  const first = parseDayKey(days[0]);
  const last = parseDayKey(days[days.length - 1]);
  if (viewMode === "day" || days.length === 1) {
    return first.toLocaleDateString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }
  const sameMonth = first.getMonth() === last.getMonth() && first.getFullYear() === last.getFullYear();
  if (sameMonth) {
    return `${first.toLocaleDateString(undefined, { month: "short", day: "numeric" })} - ${last.toLocaleDateString(undefined, {
      day: "numeric",
      year: "numeric",
    })}`;
  }
  return `${first.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} - ${last.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })}`;
}

function formatTimeLabel(hour: number): string {
  return `${pad2(hour)}:00`;
}

function toTimeLabel(value: Date): string {
  return value.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function floorToStep(value: number, step: number): number {
  return Math.floor(value / step) * step;
}

function roundToStep(value: number, step: number): number {
  return Math.round(value / step) * step;
}

function minuteFromPointer(clientY: number, rect: DOMRect): number {
  const offset = clamp(clientY - rect.top, 0, rect.height);
  const raw = (offset / rect.height) * TOTAL_MINUTES;
  return clamp(floorToStep(raw, SLOT_MINUTES), 0, TOTAL_MINUTES - SLOT_MINUTES);
}

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function parseConflictItems(error: unknown): ConflictItem[] {
  const payload = (error as { response?: { data?: { conflicts?: unknown } } })?.response?.data?.conflicts;
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

function conflictHref(appointmentId: string): string {
  const encoded = encodeURIComponent(appointmentId);
  return appPath(`/dashboard/appointments?appointment_id=${encoded}#appointment-${encoded}`);
}

function statusClass(status: AppointmentStatus): string {
  if (status === "booked") {
    return "border-blue-300 bg-blue-50 text-blue-900";
  }
  if (status === "completed") {
    return "border-emerald-300 bg-emerald-50 text-emerald-900";
  }
  if (status === "cancelled") {
    return "border-rose-300 bg-rose-50 text-rose-900";
  }
  return "border-amber-300 bg-amber-50 text-amber-900";
}

function initialFormForSlot(day: string, minutes: number): AppointmentFormValues {
  return {
    customer_id: "",
    service_id: "",
    starts_at: toLocalDateTimeInput(combineDayAndMinutes(day, minutes)),
    duration_minutes: 60,
    status: "booked",
    cancelled_reason: "",
    notes: "",
  };
}

function formFromAppointment(appointment: CalendarAppointment): AppointmentFormValues {
  const startsAt = new Date(appointment.starts_at);
  const endsAt = new Date(appointment.ends_at);
  const duration = Math.round((endsAt.getTime() - startsAt.getTime()) / 60_000);
  const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : appointment.service?.duration_min || 60;

  return {
    customer_id: appointment.customer.id,
    service_id: appointment.service?.id || "",
    starts_at: toLocalDateTimeInput(startsAt),
    duration_minutes: safeDuration,
    status: appointment.status,
    cancelled_reason: appointment.cancelled_reason || "",
    notes: appointment.notes || "",
  };
}

function layoutEventsForDay(events: CalendarAppointment[], day: string): DayLayoutEvent[] {
  const dayStart = parseDayKey(day);
  const dayEnd = addDays(dayStart, 1);

  const clipped = events
    .filter((event) => {
      const startsAt = new Date(event.starts_at);
      const endsAt = new Date(event.ends_at);
      return startsAt < dayEnd && endsAt > dayStart;
    })
    .map((event) => {
      const startsAt = new Date(event.starts_at);
      const endsAt = new Date(event.ends_at);
      const startMin = clamp(minutesSinceDayStart(startsAt, day), 0, TOTAL_MINUTES);
      const rawEnd = clamp(minutesSinceDayStart(endsAt, day), 0, TOTAL_MINUTES);
      const endMin = Math.max(startMin + MIN_EVENT_MINUTES, rawEnd);
      const startsSameDay = dayKeyFromDate(startsAt) === day;
      const endsSameDay = dayKeyFromDate(endsAt) === day;
      return {
        appointment: event,
        day,
        startMin,
        endMin,
        col: 0,
        cols: 1,
        canResize: startsSameDay && endsSameDay,
      };
    })
    .sort((a, b) => {
      if (a.startMin !== b.startMin) {
        return a.startMin - b.startMin;
      }
      if (a.endMin !== b.endMin) {
        return a.endMin - b.endMin;
      }
      return a.appointment.id.localeCompare(b.appointment.id);
    });

  const groups: DayLayoutEvent[][] = [];
  let current: DayLayoutEvent[] = [];
  let currentGroupEnd = -1;

  for (const event of clipped) {
    if (current.length === 0 || event.startMin < currentGroupEnd) {
      current.push(event);
      currentGroupEnd = Math.max(currentGroupEnd, event.endMin);
      continue;
    }
    groups.push(current);
    current = [event];
    currentGroupEnd = event.endMin;
  }
  if (current.length > 0) {
    groups.push(current);
  }

  const result: DayLayoutEvent[] = [];

  for (const group of groups) {
    const active: Array<{ endMin: number; col: number }> = [];
    const placed: DayLayoutEvent[] = [];
    let maxCols = 1;

    for (const event of group) {
      for (let i = active.length - 1; i >= 0; i -= 1) {
        if (active[i].endMin <= event.startMin) {
          active.splice(i, 1);
        }
      }

      const used = new Set(active.map((entry) => entry.col));
      let col = 0;
      while (used.has(col)) {
        col += 1;
      }

      active.push({ endMin: event.endMin, col });
      maxCols = Math.max(maxCols, col + 1);
      placed.push({ ...event, col });
    }

    for (const event of placed) {
      result.push({ ...event, cols: maxCols });
    }
  }

  return result;
}

export default function CalendarPage() {
  const { defaultLocation, isLoading: isLoadingDefaultLocation } = useDefaultLocation();

  const [viewMode, setViewMode] = useState<"week" | "day">("week");
  const viewModeOverriddenByUserRef = useRef(false);
  const [anchorDay, setAnchorDay] = useState(() => dayKeyFromDate(new Date()));

  const [appointments, setAppointments] = useState<CalendarAppointment[]>([]);
  const [services, setServices] = useState<AppointmentServiceOption[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);

  const [panelMode, setPanelMode] = useState<"create" | "edit" | null>(null);
  const [createForm, setCreateForm] = useState<AppointmentFormValues>(() => initialFormForSlot(dayKeyFromDate(new Date()), 9 * 60));
  const [editForm, setEditForm] = useState<AppointmentFormValues>(() => initialFormForSlot(dayKeyFromDate(new Date()), 9 * 60));
  const [editingId, setEditingId] = useState<string | null>(null);

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [resizeState, setResizeState] = useState<ResizeState | null>(null);
  const [resizePreviewEndById, setResizePreviewEndById] = useState<Record<string, number>>({});
  const resizePreviewRef = useRef<Record<string, number>>({});

  const [conflictToast, setConflictToast] = useState<ConflictItem[] | null>(null);

  const editingAppointment = useMemo(
    () => (editingId ? appointments.find((item) => item.id === editingId) || null : null),
    [appointments, editingId],
  );

  const appointmentsById = useMemo(() => Object.fromEntries(appointments.map((item) => [item.id, item])), [appointments]);

  const customerNameById = useMemo(() => {
    const pairs = appointments.map((item) => [item.customer.id, item.customer.name]);
    return Object.fromEntries(pairs);
  }, [appointments]);

  const visibleDays = useMemo(() => {
    const anchor = parseDayKey(anchorDay);
    if (viewMode === "day") {
      return [dayKeyFromDate(anchor)];
    }
    const weekStart = startOfWeek(anchor);
    return Array.from({ length: 7 }, (_, index) => dayKeyFromDate(addDays(weekStart, index)));
  }, [anchorDay, viewMode]);

  const rangeLabel = useMemo(() => formatRangeLabel(viewMode, visibleDays), [viewMode, visibleDays]);

  const rangeParams = useMemo(() => {
    if (visibleDays.length === 0) {
      return null;
    }
    const from = parseDayKey(visibleDays[0]);
    const to = addDays(parseDayKey(visibleDays[visibleDays.length - 1]), 1);
    return { from_dt: from.toISOString(), to_dt: to.toISOString() };
  }, [visibleDays]);

  const dayLayouts = useMemo(() => {
    return Object.fromEntries(visibleDays.map((day) => [day, layoutEventsForDay(appointments, day)])) as Record<string, DayLayoutEvent[]>;
  }, [appointments, visibleDays]);

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      try {
        const response = await api.get<CalendarTenantSettings>("/crm/settings");
        if (!active || viewModeOverriddenByUserRef.current) {
          return;
        }
        if (response.data?.calendar_default_view === "day" || response.data?.calendar_default_view === "week") {
          setViewMode(response.data.calendar_default_view);
        }
      } catch {
        // ignore and fallback to week
      }
    }

    void loadSettings();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadServices() {
      try {
        const response = await api.get<Paginated<AppointmentServiceOption>>("/crm/services", {
          params: { page: 1, page_size: 200, include_inactive: true, sort: "name", order: "asc" },
        });
        if (!active) {
          return;
        }
        setServices(response.data?.items ?? []);
      } catch {
        // silent; create/edit form keeps working without preset options
      }
    }

    void loadServices();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadCalendar() {
      if (!rangeParams) {
        return;
      }
      if (!defaultLocation?.id) {
        if (!isLoadingDefaultLocation) {
          setError("Default location is not available.");
        }
        setAppointments([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await api.get<CalendarResponse>("/crm/calendar", {
          params: {
            from_dt: rangeParams.from_dt,
            to_dt: rangeParams.to_dt,
            location_id: defaultLocation.id,
          },
        });

        if (!active) {
          return;
        }

        setAppointments(response.data?.items ?? []);
      } catch (requestError) {
        if (!active) {
          return;
        }
        setError(toErrorMessage(requestError, "Unable to load calendar."));
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadCalendar();

    return () => {
      active = false;
    };
  }, [defaultLocation?.id, isLoadingDefaultLocation, rangeParams, reloadNonce]);

  useEffect(() => {
    if (!editingId) {
      return;
    }
    if (!editingAppointment && panelMode === "edit") {
      setPanelMode(null);
      setEditingId(null);
    }
  }, [editingAppointment, editingId, panelMode]);

  useEffect(() => {
    if (!conflictToast) {
      return;
    }
    const timer = window.setTimeout(() => setConflictToast(null), 7000);
    return () => window.clearTimeout(timer);
  }, [conflictToast]);

  useEffect(() => {
    if (!resizeState) {
      return;
    }

    const onMouseMove = (event: MouseEvent) => {
      const deltaMinutes = (event.clientY - resizeState.startY) / PIXELS_PER_MINUTE;
      const rawEnd = resizeState.initialEndMin + deltaMinutes;
      const snapped = roundToStep(rawEnd, RESIZE_SNAP_MINUTES);
      const nextEnd = clamp(snapped, resizeState.startMin + MIN_EVENT_MINUTES, TOTAL_MINUTES);

      resizePreviewRef.current = {
        ...resizePreviewRef.current,
        [resizeState.appointmentId]: nextEnd,
      };
      setResizePreviewEndById((prev) => ({ ...prev, [resizeState.appointmentId]: nextEnd }));
    };

    const onMouseUp = () => {
      const current = resizePreviewRef.current[resizeState.appointmentId] ?? resizeState.initialEndMin;
      const appointment = appointmentsById[resizeState.appointmentId];

      setResizeState(null);
      resizePreviewRef.current = Object.fromEntries(
        Object.entries(resizePreviewRef.current).filter(([key]) => key !== resizeState.appointmentId),
      );
      setResizePreviewEndById((prev) => {
        const next = { ...prev };
        delete next[resizeState.appointmentId];
        return next;
      });

      if (!appointment || current === resizeState.initialEndMin) {
        return;
      }

      const startsAt = new Date(appointment.starts_at);
      const endsAt = combineDayAndMinutes(resizeState.day, current);

      if (endsAt <= startsAt) {
        return;
      }

      void patchAppointmentTimes(appointment.id, startsAt, endsAt, "Unable to resize appointment.");
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [appointmentsById, resizeState]);

  async function patchAppointmentTimes(
    appointmentId: string,
    startsAt: Date,
    endsAt: Date,
    fallbackMessage: string,
  ): Promise<void> {
    try {
      await api.patch(`/crm/appointments/${appointmentId}`, {
        starts_at: startsAt.toISOString(),
        ends_at: endsAt.toISOString(),
      });
      setReloadNonce((prev) => prev + 1);
    } catch (requestError) {
      if ((requestError as { response?: { status?: number } })?.response?.status === 409) {
        setConflictToast(parseConflictItems(requestError));
        return;
      }
      setError(toErrorMessage(requestError, fallbackMessage));
    }
  }

  function openCreateAt(day: string, minute: number) {
    setEditingId(null);
    setCreateForm(initialFormForSlot(day, minute));
    setPanelMode("create");
  }

  function openEdit(appointment: CalendarAppointment) {
    setEditingId(appointment.id);
    setEditForm(formFromAppointment(appointment));
    setPanelMode("edit");
  }

  async function onCreateSubmit(payload: AppointmentSubmitPayload) {
    await api.post("/crm/appointments", payload);
    setPanelMode(null);
    setReloadNonce((prev) => prev + 1);
  }

  async function onEditSubmit(payload: AppointmentSubmitPayload) {
    if (!editingId) {
      return;
    }
    await api.patch(`/crm/appointments/${editingId}`, payload);
    setPanelMode(null);
    setEditingId(null);
    setReloadNonce((prev) => prev + 1);
  }

  async function onDropAppointment(day: string, event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();

    const appointmentId =
      event.dataTransfer.getData("application/x-appointment-id") || event.dataTransfer.getData("text/plain");
    if (!appointmentId) {
      return;
    }

    const appointment = appointmentsById[appointmentId];
    if (!appointment) {
      return;
    }

    const minute = minuteFromPointer(event.clientY, event.currentTarget.getBoundingClientRect());
    const startsAt = combineDayAndMinutes(day, minute);

    const oldStartsAt = new Date(appointment.starts_at);
    const oldEndsAt = new Date(appointment.ends_at);
    const duration = Math.max(MIN_EVENT_MINUTES, Math.round((oldEndsAt.getTime() - oldStartsAt.getTime()) / 60_000));
    const endsAt = new Date(startsAt.getTime() + duration * 60_000);

    if (startsAt.toISOString() === appointment.starts_at && endsAt.toISOString() === appointment.ends_at) {
      return;
    }

    await patchAppointmentTimes(appointmentId, startsAt, endsAt, "Unable to move appointment.");
  }

  function shiftAnchor(amount: number) {
    const current = parseDayKey(anchorDay);
    setAnchorDay(dayKeyFromDate(addDays(current, amount)));
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Calendar</CardTitle>
            <p className="text-sm text-slate-500">{rangeLabel}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" variant="secondary" onClick={() => shiftAnchor(viewMode === "week" ? -7 : -1)}>
              Previous
            </Button>
            <Button type="button" variant="secondary" onClick={() => setAnchorDay(dayKeyFromDate(new Date()))}>
              Today
            </Button>
            <Button type="button" variant="secondary" onClick={() => shiftAnchor(viewMode === "week" ? 7 : 1)}>
              Next
            </Button>

            <div className="ml-2 flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-1">
              <Button
                type="button"
                variant={viewMode === "week" ? "primary" : "ghost"}
                className="px-3 py-1"
                onClick={() => {
                  viewModeOverriddenByUserRef.current = true;
                  setViewMode("week");
                }}
              >
                Week
              </Button>
              <Button
                type="button"
                variant={viewMode === "day" ? "primary" : "ghost"}
                className="px-3 py-1"
                onClick={() => {
                  viewModeOverriddenByUserRef.current = true;
                  setViewMode("day");
                }}
              >
                Day
              </Button>
            </div>

            <Input
              type="date"
              value={anchorDay}
              onChange={(event) => setAnchorDay(event.target.value)}
              className="ml-2 w-44"
            />
          </div>
        </CardHeader>
      </Card>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      ) : null}

      {isLoading ? <p className="text-sm text-slate-500">Loading calendar...</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
        <div
          className="min-w-[960px]"
          style={{ minWidth: `${80 + visibleDays.length * 180}px` }}
        >
          <div
            className="grid border-b border-slate-200 bg-slate-50"
            style={{ gridTemplateColumns: `80px repeat(${visibleDays.length}, minmax(0, 1fr))` }}
          >
            <div className="px-2 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Time</div>
            {visibleDays.map((day) => (
              <div key={day} className="border-l border-slate-200 px-2 py-2 text-sm font-semibold text-slate-700">
                {formatDayHeader(day)}
              </div>
            ))}
          </div>

          <div
            className="grid"
            style={{ gridTemplateColumns: `80px repeat(${visibleDays.length}, minmax(0, 1fr))` }}
          >
            <div className="relative border-r border-slate-200 bg-slate-50" style={{ height: `${GRID_HEIGHT_PX}px` }}>
              {Array.from({ length: 24 }).map((_, hour) => (
                <div
                  key={hour}
                  className="absolute left-0 right-0 px-2 text-[11px] font-medium text-slate-500"
                  style={{ top: `${hour * 60 * PIXELS_PER_MINUTE - 8}px` }}
                >
                  {formatTimeLabel(hour)}
                </div>
              ))}
            </div>

            {visibleDays.map((day) => {
              const events = dayLayouts[day] ?? [];
              return (
                <div
                  key={day}
                  className="relative border-l border-slate-200"
                  style={{ height: `${GRID_HEIGHT_PX}px` }}
                  onClick={(event) => {
                    const minute = minuteFromPointer(event.clientY, event.currentTarget.getBoundingClientRect());
                    openCreateAt(day, minute);
                  }}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) => void onDropAppointment(day, event)}
                >
                  {Array.from({ length: TOTAL_MINUTES / SLOT_MINUTES + 1 }).map((_, slot) => (
                    <div
                      key={`${day}-line-${slot}`}
                      className={`absolute inset-x-0 ${slot % 2 === 0 ? "border-t border-slate-100" : "border-t border-slate-50"}`}
                      style={{ top: `${slot * SLOT_HEIGHT_PX}px` }}
                    />
                  ))}

                  {events.map((event) => {
                    const previewEnd = resizePreviewEndById[event.appointment.id] ?? event.endMin;
                    const startDate = combineDayAndMinutes(day, event.startMin);
                    const endDate = combineDayAndMinutes(day, previewEnd);
                    const widthPct = 100 / event.cols;
                    const leftPct = event.col * widthPct;

                    return (
                      <div
                        key={`${day}-${event.appointment.id}`}
                        draggable
                        onDragStart={(dragEvent) => {
                          dragEvent.dataTransfer.setData("application/x-appointment-id", event.appointment.id);
                          dragEvent.dataTransfer.setData("text/plain", event.appointment.id);
                          setDraggingId(event.appointment.id);
                        }}
                        onDragEnd={() => setDraggingId(null)}
                        onClick={(clickEvent) => {
                          clickEvent.stopPropagation();
                          openEdit(event.appointment);
                        }}
                        className={`absolute rounded-lg border p-2 text-xs shadow-sm ${statusClass(event.appointment.status)} ${
                          draggingId === event.appointment.id ? "opacity-60" : "opacity-100"
                        }`}
                        style={{
                          top: `${event.startMin * PIXELS_PER_MINUTE}px`,
                          height: `${Math.max((previewEnd - event.startMin) * PIXELS_PER_MINUTE, 22)}px`,
                          left: `calc(${leftPct}% + 2px)`,
                          width: `calc(${widthPct}% - 4px)`,
                          zIndex: panelMode === "edit" && editingId === event.appointment.id ? 20 : 10,
                        }}
                      >
                        <p className="truncate font-semibold">{event.appointment.customer.name}</p>
                        <p className="truncate">{toTimeLabel(startDate)} - {toTimeLabel(endDate)}</p>
                        <p className="truncate">{event.appointment.service?.name || "No service"}</p>

                        {event.canResize ? (
                          <div
                            role="presentation"
                            className="absolute inset-x-1 bottom-0 h-2 cursor-ns-resize rounded-b bg-black/10"
                            onMouseDown={(mouseEvent) => {
                              mouseEvent.stopPropagation();
                              mouseEvent.preventDefault();
                              resizePreviewRef.current = {
                                ...resizePreviewRef.current,
                                [event.appointment.id]: event.endMin,
                              };
                              setResizePreviewEndById((prev) => ({ ...prev, [event.appointment.id]: event.endMin }));
                              setResizeState({
                                appointmentId: event.appointment.id,
                                day,
                                startMin: event.startMin,
                                initialEndMin: event.endMin,
                                startY: mouseEvent.clientY,
                              });
                            }}
                          />
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {panelMode ? (
        <div className="fixed inset-0 z-40 bg-black/20">
          <aside className="absolute right-0 top-0 h-full w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white p-4 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">
                {panelMode === "create" ? "Quick create appointment" : "Edit appointment"}
              </h3>
              <Button type="button" variant="secondary" onClick={() => setPanelMode(null)}>
                Close
              </Button>
            </div>

            {panelMode === "create" ? (
              <AppointmentForm
                mode="create"
                values={createForm}
                onChange={setCreateForm}
                onSubmit={onCreateSubmit}
                services={services}
                defaultLocationId={defaultLocation?.id ?? null}
                customerNameById={customerNameById}
                disabled={isLoadingDefaultLocation}
                onCancel={() => setPanelMode(null)}
                submitLabel="Create"
                submittingLabel="Creating..."
                conflictHrefForId={conflictHref}
              />
            ) : (
              <AppointmentForm
                mode="edit"
                values={editForm}
                onChange={setEditForm}
                onSubmit={onEditSubmit}
                services={services}
                defaultLocationId={defaultLocation?.id ?? editingAppointment?.location_id ?? null}
                customerNameById={customerNameById}
                onCancel={() => setPanelMode(null)}
                submitLabel="Save"
                submittingLabel="Saving..."
                conflictHrefForId={conflictHref}
              />
            )}
          </aside>
        </div>
      ) : null}

      {conflictToast ? (
        <div className="pointer-events-none fixed right-4 top-4 z-50 w-full max-w-md">
          <div className="pointer-events-auto rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 shadow-lg">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold">Time slot conflicts with another appointment</p>
                <div className="mt-2 space-y-2 text-xs text-amber-800">
                  {conflictToast.slice(0, 3).map((item) => {
                    const conflict = appointmentsById[item.id];
                    const starts = new Date(item.starts_at);
                    const ends = new Date(item.ends_at);
                    return (
                      <div key={item.id} className="rounded border border-amber-200 bg-amber-100/40 p-2">
                        <p className="font-semibold">{conflict?.customer.name || "Existing appointment"}</p>
                        <p>
                          {starts.toLocaleString()} - {ends.toLocaleString()}
                        </p>
                        <a className="underline" href={conflictHref(item.id)}>
                          Open appointment
                        </a>
                      </div>
                    );
                  })}
                </div>
              </div>
              <button
                type="button"
                className="rounded-md border border-amber-300 px-2 py-1 text-xs hover:bg-amber-100"
                onClick={() => setConflictToast(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
