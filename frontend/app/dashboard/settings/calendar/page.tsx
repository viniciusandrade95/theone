"use client";

import { useEffect, useState } from "react";

import { SettingsNav } from "@/components/dashboard/SettingsNav";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { CalendarDefaultView, TenantSettings, TenantSettingsUpdatePayload } from "@/lib/contracts/settings";
import { api } from "@/lib/api";

type CalendarTenantSettings = Pick<TenantSettings, "calendar_default_view">;

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string; error?: string } } })?.response;
  return response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

export default function SettingsCalendarPage() {
  const [calendarDefaultView, setCalendarDefaultView] = useState<CalendarDefaultView>("week");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<CalendarTenantSettings>("/crm/settings");
        if (!active) {
          return;
        }
        if (response.data?.calendar_default_view === "day" || response.data?.calendar_default_view === "week") {
          setCalendarDefaultView(response.data.calendar_default_view);
        }
      } catch (requestError) {
        if (active) {
          setError(toErrorMessage(requestError, "Unable to load calendar settings."));
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload: TenantSettingsUpdatePayload = { calendar_default_view: calendarDefaultView };
      await api.put("/crm/settings", payload);
      setSuccessMessage("Calendar settings updated.");
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update calendar settings."));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsNav />

      <Card>
        <CardHeader>
          <CardTitle>Calendar settings</CardTitle>
          <CardDescription>Define the default view opened in the calendar module.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          {successMessage ? (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{successMessage}</p>
          ) : null}

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading settings...</p>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <label className="space-y-1 text-sm font-medium text-slate-700">
                Default calendar view
                <select
                  className="h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
                  value={calendarDefaultView}
                  onChange={(event) => setCalendarDefaultView(event.target.value === "day" ? "day" : "week")}
                >
                  <option value="week">Week</option>
                  <option value="day">Day</option>
                </select>
              </label>

              <Button type="submit" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save calendar settings"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
