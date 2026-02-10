"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, KeyboardEvent, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useDefaultLocation } from "@/lib/default-location";
import { appPath } from "@/lib/paths";

type Stage = "lead" | "booked" | "completed";

type FormErrors = {
  name?: string;
  email?: string;
  global?: string;
};

function toErrorMessage(error: unknown): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string; error?: string } } })?.response;
  return response?.data?.message || response?.data?.detail || response?.data?.error || "Unable to create customer.";
}

function parseEmail(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function parsePhone(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function validateForm(name: string, email: string): FormErrors {
  const errors: FormErrors = {};
  if (!name.trim()) {
    errors.name = "Name is required.";
  }
  if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  return errors;
}

export default function NewCustomerPage() {
  const router = useRouter();
  const { defaultLocation } = useDefaultLocation();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [stage, setStage] = useState<Stage>("lead");
  const [consentMarketing, setConsentMarketing] = useState(false);
  const [consentAt, setConsentAt] = useState("");

  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const primaryLocationId = useMemo(() => defaultLocation?.id ?? "", [defaultLocation?.id]);

  function addTag(value: string) {
    const next = value.trim().toLowerCase();
    if (!next || tags.includes(next)) {
      return;
    }
    setTags((prev) => [...prev, next]);
  }

  function handleTagsKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      if (!tagInput.trim()) {
        return;
      }
      addTag(tagInput);
      setTagInput("");
    }
  }

  function removeTag(value: string) {
    setTags((prev) => prev.filter((tag) => tag !== value));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationErrors = validateForm(name, email);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await api.post("/crm/customers", {
        name: name.trim(),
        phone: parsePhone(phone),
        email: parseEmail(email),
        tags,
        stage,
        consent_marketing: consentMarketing,
        consent_marketing_at: consentAt ? new Date(consentAt).toISOString() : null,
      });

      const customerId = response.data?.id as string | undefined;
      if (!customerId) {
        throw new Error("Missing customer id in response");
      }

      router.push(appPath(`/dashboard/customers/${customerId}`));
    } catch (submitError) {
      const message = toErrorMessage(submitError);
      setErrors((prev) => ({ ...prev, global: message }));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Create customer</h1>
          <p className="text-sm text-slate-500">Add a new contact with lifecycle and consent information.</p>
        </div>
        <Link href={appPath("/dashboard/customers")}>
          <Button variant="secondary">Back to list</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Customer profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input type="hidden" name="primary_location_id" value={primaryLocationId} readOnly />

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Name
                <Input value={name} onChange={(event) => setName(event.target.value)} required />
                {errors.name ? <span className="text-xs text-red-600">{errors.name}</span> : null}
              </label>

              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Stage
                <select
                  value={stage}
                  onChange={(event) => setStage(event.target.value as Stage)}
                  className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
                >
                  <option value="lead">Lead</option>
                  <option value="booked">Booked</option>
                  <option value="completed">Completed</option>
                </select>
              </label>

              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Phone
                <Input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Recommended" />
              </label>

              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Email
                <Input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="Optional"
                />
                {errors.email ? <span className="text-xs text-red-600">{errors.email}</span> : null}
              </label>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-700">Tags</p>
              <Input
                value={tagInput}
                onChange={(event) => setTagInput(event.target.value)}
                onKeyDown={handleTagsKeyDown}
                onBlur={() => {
                  if (tagInput.trim()) {
                    addTag(tagInput);
                    setTagInput("");
                  }
                }}
                placeholder="Type tag and press Enter"
              />
              {tags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"
                    >
                      {tag} ×
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="space-y-3 rounded-xl border border-slate-200 p-3">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={consentMarketing}
                  onChange={(event) => setConsentMarketing(event.target.checked)}
                />
                Marketing consent granted
              </label>

              {consentMarketing ? (
                <label className="space-y-2 text-sm font-semibold text-slate-700">
                  Consent timestamp (optional)
                  <input
                    type="datetime-local"
                    value={consentAt}
                    onChange={(event) => setConsentAt(event.target.value)}
                    className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
                  />
                </label>
              ) : null}
            </div>

            {errors.global ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{errors.global}</div>
            ) : null}

            <div className="flex items-center justify-end gap-2">
              <Link href={appPath("/dashboard/customers")}>
                <Button type="button" variant="secondary">Cancel</Button>
              </Link>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create customer"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
