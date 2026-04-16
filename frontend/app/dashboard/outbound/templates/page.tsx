"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { MessageTemplate, OutboundChannel, OutboundTemplateType, Paginated } from "@/lib/contracts/outbound";

type FormState = {
  name: string;
  type: OutboundTemplateType;
  channel: OutboundChannel;
  body: string;
  is_active: boolean;
};

type TemplatePreset = {
  key: string;
  label: string;
  description: string;
  type: OutboundTemplateType;
  channel: OutboundChannel;
  defaultName: string;
  defaultBody: string;
};

const TEMPLATE_TYPES: OutboundTemplateType[] = [
  "booking_confirmation",
  "reminder_24h",
  "reminder_3h",
  "post_service_followup",
  "review_request",
  "reactivation",
  "simple_campaign",
  "tomorrow_open_slot",
  "internal_followup_support",
];

const PRESETS: TemplatePreset[] = [
  {
    key: "booking_confirmation",
    label: "Booking confirmation",
    description: "Confirm a booking with date/time + business name.",
    type: "booking_confirmation",
    channel: "whatsapp",
    defaultName: "Booking confirmation (WhatsApp)",
    defaultBody:
      "Hi {{customer_name}}! ✅\n\nYour booking is confirmed for {{appointment_date}} at {{appointment_time}}.\n\nSee you soon,\n{{business_name}}",
  },
  {
    key: "reminder_24h",
    label: "Reminder (24h)",
    description: "Reminder one day before the appointment.",
    type: "reminder_24h",
    channel: "whatsapp",
    defaultName: "Reminder 24h (WhatsApp)",
    defaultBody:
      "Hi {{customer_name}}! Friendly reminder: you have an appointment tomorrow ({{appointment_date}}) at {{appointment_time}}.\n\n— {{business_name}}",
  },
  {
    key: "reminder_3h",
    label: "Reminder (3h)",
    description: "Last-minute reminder shortly before the appointment.",
    type: "reminder_3h",
    channel: "whatsapp",
    defaultName: "Reminder 3h (WhatsApp)",
    defaultBody:
      "Hi {{customer_name}}! Reminder: your appointment is today at {{appointment_time}}.\n\nSee you soon,\n{{business_name}}",
  },
  {
    key: "reactivation",
    label: "Reactivation",
    description: "Invite customers back after a period of inactivity.",
    type: "reactivation",
    channel: "whatsapp",
    defaultName: "Reactivation (WhatsApp)",
    defaultBody:
      "Hi {{customer_name}}! We miss you at {{business_name}}.\n\nWant to book a new appointment this week?",
  },
  {
    key: "internal_summary",
    label: "Business summary (manual)",
    description: "A placeholder for reporting; send to an internal recipient (see docs).",
    type: "internal_followup_support",
    channel: "whatsapp",
    defaultName: "Business summary (manual)",
    defaultBody:
      "Daily summary – {{business_name}}\n\n- Today: [fill]\n- Tomorrow: [fill]\n- Notes: [fill]\n\n(Reporting automation is a future step.)",
  },
];

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function defaultForm(): FormState {
  return {
    name: "",
    type: "simple_campaign",
    channel: "whatsapp",
    body: "Hi {{customer_name}},\n\n",
    is_active: true,
  };
}

export default function OutboundTemplatesPage() {
  const [items, setItems] = useState<MessageTemplate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  const [typeFilter, setTypeFilter] = useState<string>("");
  const [activeFilter, setActiveFilter] = useState<string>("");

  const [createForm, setCreateForm] = useState<FormState>(defaultForm());
  const [editing, setEditing] = useState<MessageTemplate | null>(null);
  const [editForm, setEditForm] = useState<FormState>(defaultForm());

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (typeFilter.trim()) params.type = typeFilter.trim();
      if (activeFilter === "active") params.is_active = true;
      if (activeFilter === "inactive") params.is_active = false;
      const resp = await api.get<Paginated<MessageTemplate>>("/crm/outbound/templates", { params });
      setItems(resp.data.items ?? []);
      setTotal(resp.data.total ?? 0);
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to load templates."));
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, typeFilter, activeFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setPage(1);
  }, [typeFilter, activeFilter]);

  function applyPreset(preset: TemplatePreset) {
    setCreateForm({
      name: preset.defaultName,
      type: preset.type,
      channel: preset.channel,
      body: preset.defaultBody,
      is_active: true,
    });
    setSuccess(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function createTemplate() {
    if (!createForm.name.trim() || !createForm.body.trim()) {
      setError("Name and body are required.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post("/crm/outbound/templates", {
        name: createForm.name.trim(),
        type: createForm.type,
        channel: createForm.channel,
        body: createForm.body,
        is_active: createForm.is_active,
      });
      setCreateForm(defaultForm());
      setSuccess("Template created.");
      await load();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to create template."));
    } finally {
      setIsSaving(false);
    }
  }

  function beginEdit(tpl: MessageTemplate) {
    setEditing(tpl);
    setEditForm({
      name: tpl.name,
      type: tpl.type,
      channel: tpl.channel,
      body: tpl.body,
      is_active: tpl.is_active,
    });
  }

  async function saveEdit() {
    if (!editing) return;
    if (!editForm.name.trim() || !editForm.body.trim()) {
      setError("Name and body are required.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.patch(`/crm/outbound/templates/${editing.id}`, {
        name: editForm.name.trim(),
        type: editForm.type,
        channel: editForm.channel,
        body: editForm.body,
        is_active: editForm.is_active,
      });
      setEditing(null);
      setSuccess("Template updated.");
      await load();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update template."));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteTemplate(tpl: MessageTemplate) {
    if (!confirm(`Delete template "${tpl.name}"?`)) return;
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.delete(`/crm/outbound/templates/${tpl.id}`);
      setSuccess("Template deleted.");
      await load();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to delete template."));
    } finally {
      setIsSaving(false);
    }
  }

  async function toggleActive(tpl: MessageTemplate) {
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.patch(`/crm/outbound/templates/${tpl.id}`, { is_active: !tpl.is_active });
      await load();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to update template."));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Outbound templates</h1>
        <p className="text-sm text-slate-500">Create and manage templates for manual/triggered outbound.</p>
      </div>

      {error ? <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      {success ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Create template</CardTitle>
          <CardDescription>
            Variables supported: {"{{customer_name}} {{appointment_date}} {{appointment_time}} {{service_name}} {{location_name}} {{business_name}}"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-900">Quick start presets</p>
            <p className="mt-1 text-xs text-slate-600">Pick a common business use case and tweak the message.</p>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {PRESETS.map((preset) => (
                <button
                  key={preset.key}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm hover:border-slate-300"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold text-slate-900">{preset.label}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{preset.type}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">{preset.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Input
              value={createForm.name}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Template name"
            />
            <select
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              value={createForm.type}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, type: e.target.value as OutboundTemplateType }))}
            >
              {TEMPLATE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <input
                type="checkbox"
                checked={createForm.is_active}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, is_active: e.target.checked }))}
              />
              Active
            </label>
          </div>
          <textarea
            value={createForm.body}
            onChange={(e) => setCreateForm((prev) => ({ ...prev, body: e.target.value }))}
            className="min-h-[140px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="Template body..."
          />
          <Button type="button" disabled={isSaving} onClick={() => void createTemplate()}>
            {isSaving ? "Saving..." : "Create"}
          </Button>
        </CardContent>
      </Card>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <Input value={editForm.name} onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))} />
              <select
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                value={editForm.type}
                onChange={(e) => setEditForm((p) => ({ ...p, type: e.target.value as OutboundTemplateType }))}
              >
                {TEMPLATE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <input
                  type="checkbox"
                  checked={editForm.is_active}
                  onChange={(e) => setEditForm((p) => ({ ...p, is_active: e.target.checked }))}
                />
                Active
              </label>
            </div>
            <textarea
              value={editForm.body}
              onChange={(e) => setEditForm((p) => ({ ...p, body: e.target.value }))}
              className="min-h-[160px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            />
            <div className="flex flex-wrap gap-2">
              <Button type="button" disabled={isSaving} onClick={() => void saveEdit()}>
                {isSaving ? "Saving..." : "Save"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setEditing(null)} disabled={isSaving}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Templates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <select
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All types</option>
              {TEMPLATE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <select
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <Button type="button" variant="secondary" onClick={() => void load()} disabled={isLoading}>
              Refresh
            </Button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Name</th>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Channel</th>
                  <th className="px-4 py-3 font-semibold">Active</th>
                  <th className="px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={5}>
                      Loading templates...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-slate-500" colSpan={5}>
                      No templates found.
                    </td>
                  </tr>
                ) : (
                  items.map((tpl) => (
                    <tr key={tpl.id}>
                      <td className="px-4 py-3 font-semibold text-slate-900">{tpl.name}</td>
                      <td className="px-4 py-3 text-slate-600">{tpl.type}</td>
                      <td className="px-4 py-3 text-slate-600">{tpl.channel}</td>
                      <td className="px-4 py-3">
                        <span
                          className={[
                            "rounded-full px-2 py-0.5 text-xs font-semibold",
                            tpl.is_active ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700",
                          ].join(" ")}
                        >
                          {tpl.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button type="button" variant="secondary" onClick={() => beginEdit(tpl)} disabled={isSaving}>
                            Edit
                          </Button>
                          <Button type="button" variant="secondary" onClick={() => void toggleActive(tpl)} disabled={isSaving}>
                            {tpl.is_active ? "Disable" : "Enable"}
                          </Button>
                          <Button type="button" variant="secondary" onClick={() => void deleteTemplate(tpl)} disabled={isSaving}>
                            Delete
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
            <p className="text-sm text-slate-500">{total} template(s)</p>
            <div className="flex items-center gap-2">
              <Button type="button" variant="secondary" disabled={page <= 1 || isLoading} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                Previous
              </Button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                variant="secondary"
                disabled={page >= totalPages || isLoading}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
