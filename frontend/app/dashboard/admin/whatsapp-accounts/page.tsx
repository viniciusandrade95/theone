"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function WhatsAppAccountsPage() {
  const [provider, setProvider] = useState("meta");
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [status, setStatus] = useState("active");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const response = await api.post("/messaging/whatsapp-accounts", {
        provider,
        phone_number_id: phoneNumberId,
        status,
      });
      setMessage(`Saved account ${response.data.phone_number_id}`);
      setPhoneNumberId("");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to save WhatsApp account");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Admin</p>
        <h1 className="text-3xl font-semibold text-white">WhatsApp Accounts</h1>
        <p className="mt-2 text-sm text-slate-300">
          Map provider phone number IDs to tenants so inbound webhooks resolve safely.
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <label className="text-sm text-slate-300" htmlFor="provider">Provider</label>
            <Input
              id="provider"
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
              placeholder="meta"
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm text-slate-300" htmlFor="phoneNumberId">Phone Number ID</label>
            <Input
              id="phoneNumberId"
              value={phoneNumberId}
              onChange={(event) => setPhoneNumberId(event.target.value)}
              placeholder="pn-123"
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm text-slate-300" htmlFor="status">Status</label>
            <Input
              id="status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              placeholder="active"
              required
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save WhatsApp Account"}
          </Button>
        </form>
      </Card>

      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}
    </div>
  );
}
