"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { appPath } from "@/lib/paths";
import type { MessageTemplate, OutboundMessage, PreviewResponse, SendResponse } from "@/lib/contracts/outbound";

type Stage = "lead" | "booked" | "completed";

type Customer = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  tags: string[];
  stage: Stage;
  consent_marketing: boolean;
  created_at: string;
};

type Interaction = {
  id: string;
  type: string;
  content: string;
  created_at: string;
};

type Appointment = {
  id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  notes: string | null;
};

type OutboundTemplateList = {
  items: MessageTemplate[];
  total: number;
  page: number;
  page_size: number;
};

type OutboundMessageList = {
  items: OutboundMessage[];
  total: number;
  page: number;
  page_size: number;
};

type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

type ProfileForm = {
  name: string;
  phone: string;
  email: string;
  stage: Stage;
  consent_marketing: boolean;
};

function toErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { details?: { message?: string }; message?: string; detail?: string; error?: string } } })
    ?.response;
  return response?.data?.details?.message || response?.data?.message || response?.data?.detail || response?.data?.error || fallback;
}

function toLocalDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function CustomerDetailPage() {
  const params = useParams();
  const customerId = params.customerId as string;

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [profile, setProfile] = useState<ProfileForm>({
    name: "",
    phone: "",
    email: "",
    stage: "lead",
    consent_marketing: false,
  });

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [interactions, setInteractions] = useState<Interaction[]>([]);

  const [newTag, setNewTag] = useState("");
  const [note, setNote] = useState("");

  const [outboundTemplates, setOutboundTemplates] = useState<MessageTemplate[]>([]);
  const [outboundMessages, setOutboundMessages] = useState<OutboundMessage[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [selectedAppointmentId, setSelectedAppointmentId] = useState<string>("");
  const [preview, setPreview] = useState<string>("");
  const [finalBody, setFinalBody] = useState<string>("");
  const [lastWhatsappUrl, setLastWhatsappUrl] = useState<string | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSendingOutbound, setIsSendingOutbound] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingTags, setIsSavingTags] = useState(false);
  const [isAddingNote, setIsAddingNote] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const tags = useMemo(() => customer?.tags ?? [], [customer?.tags]);
  const selectedTemplate = useMemo(
    () => outboundTemplates.find((t) => t.id === selectedTemplateId) ?? null,
    [outboundTemplates, selectedTemplateId],
  );

  const loadCustomer = useCallback(async () => {
    if (!customerId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const from = new Date();
      from.setFullYear(from.getFullYear() - 5);
      const to = new Date();
      to.setFullYear(to.getFullYear() + 5);

      const [customerResponse, interactionsResponse, appointmentsResponse, templatesResponse, outboundResponse] = await Promise.all([
        api.get<Customer>(`/crm/customers/${customerId}`),
        api.get<Paginated<Interaction>>(`/crm/customers/${customerId}/interactions`, {
          params: { page: 1, page_size: 50, sort: "created_at", order: "desc" },
        }),
        api.get<Paginated<Appointment>>("/crm/appointments", {
          params: {
            page: 1,
            page_size: 25,
            customer_id: customerId,
            from_dt: from.toISOString(),
            to_dt: to.toISOString(),
            sort: "starts_at",
            order: "desc",
          },
        }),
        api.get<OutboundTemplateList>("/crm/outbound/templates", { params: { page: 1, page_size: 200, is_active: true } }),
        api.get<OutboundMessageList>("/crm/outbound/messages", { params: { page: 1, page_size: 50, customer_id: customerId } }),
      ]);

      const loadedCustomer = customerResponse.data;
      setCustomer(loadedCustomer);
      setProfile({
        name: loadedCustomer.name,
        phone: loadedCustomer.phone ?? "",
        email: loadedCustomer.email ?? "",
        stage: loadedCustomer.stage,
        consent_marketing: loadedCustomer.consent_marketing,
      });
      setInteractions(interactionsResponse.data?.items ?? []);
      setAppointments(appointmentsResponse.data?.items ?? []);
      setOutboundTemplates(templatesResponse.data?.items ?? []);
      setOutboundMessages(outboundResponse.data?.items ?? []);
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to load customer."));
    } finally {
      setIsLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    void loadCustomer();
  }, [loadCustomer]);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!customer) {
      return;
    }
    if (!profile.name.trim()) {
      setError("Name is required.");
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setIsSavingProfile(true);

    try {
      const response = await api.put<Customer>(`/crm/customers/${customer.id}`, {
        name: profile.name.trim(),
        phone: profile.phone.trim() || null,
        email: profile.email.trim() || null,
        stage: profile.stage,
        consent_marketing: profile.consent_marketing,
      });

      const updated = response.data;
      setCustomer(updated);
      setProfile({
        name: updated.name,
        phone: updated.phone ?? "",
        email: updated.email ?? "",
        stage: updated.stage,
        consent_marketing: updated.consent_marketing,
      });
      setSuccessMessage("Profile saved.");
    } catch (saveError) {
      setError(toErrorMessage(saveError, "Unable to save profile."));
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function saveTags(nextTags: string[]) {
    if (!customer) {
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setIsSavingTags(true);

    try {
      const response = await api.put<Customer>(`/crm/customers/${customer.id}`, {
        tags: nextTags,
      });
      setCustomer(response.data);
      setSuccessMessage("Tags updated.");
    } catch (saveError) {
      setError(toErrorMessage(saveError, "Unable to update tags."));
    } finally {
      setIsSavingTags(false);
    }
  }

  async function addTag() {
    const candidate = newTag.trim().toLowerCase();
    if (!candidate || tags.includes(candidate)) {
      setNewTag("");
      return;
    }
    await saveTags([...tags, candidate]);
    setNewTag("");
  }

  async function removeTag(tag: string) {
    await saveTags(tags.filter((value) => value !== tag));
  }

  async function submitNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!customer) {
      return;
    }

    const content = note.trim();
    if (!content) {
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setIsAddingNote(true);

    try {
      const response = await api.post<Interaction>(`/crm/customers/${customer.id}/interactions`, {
        type: "note",
        content,
      });

      setInteractions((prev) => [response.data, ...prev]);
      setNote("");
      setSuccessMessage("Note added.");
    } catch (addError) {
      setError(toErrorMessage(addError, "Unable to add note."));
    } finally {
      setIsAddingNote(false);
    }
  }

  async function refreshOutboundHistory() {
    if (!customer) return;
    try {
      const outboundResponse = await api.get<OutboundMessageList>("/crm/outbound/messages", {
        params: { page: 1, page_size: 50, customer_id: customer.id },
      });
      setOutboundMessages(outboundResponse.data?.items ?? []);
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to load outbound history."));
    }
  }

  async function doPreview() {
    if (!customer) return;
    if (!selectedTemplateId) {
      setError("Select a template first.");
      return;
    }
    setIsPreviewing(true);
    setError(null);
    setSuccessMessage(null);
    setLastWhatsappUrl(null);
    try {
      const resp = await api.post<PreviewResponse>("/crm/outbound/preview", {
        customer_id: customer.id,
        appointment_id: selectedAppointmentId || null,
        template_id: selectedTemplateId,
      });
      setPreview(resp.data.rendered_body);
      setFinalBody(resp.data.rendered_body);
      setSuccessMessage("Preview generated.");
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to preview message."));
    } finally {
      setIsPreviewing(false);
    }
  }

  async function doSend() {
    if (!customer) return;
    if (!selectedTemplate) {
      setError("Select a template first.");
      return;
    }
    if (!finalBody.trim()) {
      setError("Message body is required.");
      return;
    }

    setIsSendingOutbound(true);
    setError(null);
    setSuccessMessage(null);
    setLastWhatsappUrl(null);
    try {
      const resp = await api.post<SendResponse>("/crm/outbound/send", {
        customer_id: customer.id,
        appointment_id: selectedAppointmentId || null,
        template_id: selectedTemplate.id,
        final_body: finalBody,
        type: selectedTemplate.type,
        channel: selectedTemplate.channel,
      });
      if (resp.data.ok) {
        if (resp.data.whatsapp_url) {
          setSuccessMessage("Message prepared. Open WhatsApp to send.");
        } else {
          setSuccessMessage(resp.data.note ?? "Message sent.");
        }
        setLastWhatsappUrl(resp.data.whatsapp_url ?? null);
        setPreview(resp.data.outbound_message.rendered_body);
        await refreshOutboundHistory();
      } else {
        setError(resp.data.note ?? "Unable to prepare message.");
        await refreshOutboundHistory();
      }
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to send message."));
    } finally {
      setIsSendingOutbound(false);
    }
  }

  async function resendOutbound(messageId: string) {
    setError(null);
    setSuccessMessage(null);
    setLastWhatsappUrl(null);
    try {
      const resp = await api.post<SendResponse>(`/crm/outbound/${messageId}/resend`);
      if (resp.data.ok) {
        if (resp.data.whatsapp_url) {
          setSuccessMessage("Message prepared again. Open WhatsApp to send.");
        } else {
          setSuccessMessage(resp.data.note ?? "Message sent.");
        }
        setLastWhatsappUrl(resp.data.whatsapp_url ?? null);
      } else {
        setError(resp.data.note ?? "Unable to resend message.");
      }
      await refreshOutboundHistory();
    } catch (requestError) {
      setError(toErrorMessage(requestError, "Unable to resend message."));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Customer profile</h1>
          <p className="text-sm text-slate-500">Edit profile data, manage tags, and keep a timeline of notes.</p>
        </div>
        <Link href={appPath("/dashboard/customers")}>
          <Button variant="secondary">Back to customers</Button>
        </Link>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      ) : null}
      {successMessage ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{successMessage}</div>
      ) : null}

      {isLoading && !customer ? <p className="text-sm text-slate-500">Loading customer...</p> : null}

      {!isLoading && !customer ? <p className="text-sm text-slate-500">Customer not found.</p> : null}

      {customer ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={saveProfile} className="space-y-4">
                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Name
                  <Input
                    value={profile.name}
                    onChange={(event) => setProfile((prev) => ({ ...prev, name: event.target.value }))}
                    required
                  />
                </label>

                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Phone
                  <Input
                    value={profile.phone}
                    onChange={(event) => setProfile((prev) => ({ ...prev, phone: event.target.value }))}
                  />
                </label>

                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Email
                  <Input
                    type="email"
                    value={profile.email}
                    onChange={(event) => setProfile((prev) => ({ ...prev, email: event.target.value }))}
                  />
                </label>

                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Stage
                  <select
                    value={profile.stage}
                    onChange={(event) => setProfile((prev) => ({ ...prev, stage: event.target.value as Stage }))}
                    className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
                  >
                    <option value="lead">Lead</option>
                    <option value="booked">Booked</option>
                    <option value="completed">Completed</option>
                  </select>
                </label>

                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={profile.consent_marketing}
                    onChange={(event) =>
                      setProfile((prev) => ({ ...prev, consent_marketing: event.target.checked }))
                    }
                  />
                  Marketing consent
                </label>

                <p className="text-xs text-slate-500">Created at: {toLocalDateTime(customer.created_at)}</p>

                <Button type="submit" disabled={isSavingProfile}>
                  {isSavingProfile ? "Saving..." : "Save profile"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tags</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Input
                  value={newTag}
                  onChange={(event) => setNewTag(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      void addTag();
                    }
                  }}
                  placeholder="Add a tag"
                />
                <Button type="button" variant="secondary" disabled={isSavingTags} onClick={() => void addTag()}>
                  Add
                </Button>
              </div>

              {tags.length === 0 ? (
                <p className="text-sm text-slate-500">No tags yet.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => void removeTag(tag)}
                      disabled={isSavingTags}
                      className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 disabled:opacity-60"
                    >
                      {tag} ×
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={submitNote} className="space-y-3">
                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Add note
                  <Input
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="Write an interaction note"
                  />
                </label>
                <Button type="submit" disabled={isAddingNote}>
                  {isAddingNote ? "Saving..." : "Add note"}
                </Button>
              </form>

              {interactions.length === 0 ? (
                <p className="text-sm text-slate-500">No interactions yet.</p>
              ) : (
                <ul className="space-y-3">
                  {interactions.map((interaction) => (
                    <li key={interaction.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                      <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
                        <span className="font-semibold uppercase">{interaction.type}</span>
                        <span>{toLocalDateTime(interaction.created_at)}</span>
                      </div>
                      <p className="mt-2 text-slate-700">{interaction.content}</p>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Outbound (WhatsApp)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-slate-500">
                MVP note: status <span className="font-mono">sent</span> means user-assisted send was initiated (not provider delivery confirmation).
              </p>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Template</p>
                  <select
                    className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
                    value={selectedTemplateId}
                    onChange={(e) => {
                      setSelectedTemplateId(e.target.value);
                      setPreview("");
                      setFinalBody("");
                    }}
                  >
                    <option value="">Select a template...</option>
                    {outboundTemplates.map((tpl) => (
                      <option key={tpl.id} value={tpl.id}>
                        {tpl.name} ({tpl.type})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-700">Appointment (optional)</p>
                  <select
                    className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
                    value={selectedAppointmentId}
                    onChange={(e) => setSelectedAppointmentId(e.target.value)}
                  >
                    <option value="">No appointment</option>
                    {appointments.map((a) => (
                      <option key={a.id} value={a.id}>
                        {toLocalDateTime(a.starts_at)} ({a.status})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="secondary" disabled={isPreviewing || !selectedTemplateId} onClick={() => void doPreview()}>
                  {isPreviewing ? "Previewing..." : "Preview"}
                </Button>
                <Button type="button" disabled={isSendingOutbound || !selectedTemplateId} onClick={() => void doSend()}>
                  {isSendingOutbound ? "Preparing..." : "Prepare send"}
                </Button>
                {lastWhatsappUrl ? (
                  <a href={lastWhatsappUrl} target="_blank" rel="noreferrer" className="text-sm font-semibold text-slate-700 underline">
                    Open WhatsApp
                  </a>
                ) : null}
              </div>

              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-700">Message</p>
                <textarea
                  value={finalBody}
                  onChange={(e) => setFinalBody(e.target.value)}
                  className="min-h-[140px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                  placeholder="Generate a preview or write a custom message..."
                />
                {preview ? <p className="text-xs text-slate-500">Preview generated. You can edit the final message before sending.</p> : null}
              </div>

              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-700">Outbound history</p>
                {outboundMessages.length === 0 ? (
                  <p className="text-sm text-slate-500">No outbound messages yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {outboundMessages.map((m) => (
                      <li key={m.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-xs font-semibold uppercase text-slate-500">
                            {m.type} · {m.status}
                          </span>
                          <span className="text-xs text-slate-500">{toLocalDateTime(m.created_at)}</span>
                        </div>
                        <p className="mt-2 whitespace-pre-wrap text-slate-700">{m.rendered_body}</p>
                        {m.error_message ? <p className="mt-2 text-xs text-red-700">Error: {m.error_message}</p> : null}
                        {m.status === "failed" ? (
                          <div className="mt-2">
                            <Button type="button" variant="secondary" onClick={() => void resendOutbound(m.id)}>
                              Resend
                            </Button>
                          </div>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Appointment history</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Link href={appPath(`/dashboard/appointments?customer_id=${customer.id}`)}>
                <Button variant="secondary">Create appointment for this customer</Button>
              </Link>

              {appointments.length === 0 ? (
                <p className="text-sm text-slate-500">No appointments found.</p>
              ) : (
                <ul className="space-y-3">
                  {appointments.map((appointment) => (
                    <li key={appointment.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold capitalize text-slate-900">{appointment.status}</span>
                        <span className="text-xs text-slate-500">
                          {toLocalDateTime(appointment.starts_at)} - {toLocalDateTime(appointment.ends_at)}
                        </span>
                      </div>
                      {appointment.notes ? <p className="mt-2 text-slate-600">{appointment.notes}</p> : null}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
