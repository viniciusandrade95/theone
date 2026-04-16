"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type WhatsAppAccount = {
  id: string;
  tenant_id: string;
  provider: string;
  phone_number_id: string;
  status: string;
  created_at?: string | null;
};

type WhatsAppConnection = {
  webhook_secret_configured: boolean;
  webhook_verify_token_configured: boolean;
  cloud_access_token_configured: boolean;
  cloud_api_version: string;
  last_delivery_callback_received_at?: string | null;
};

type WhatsAppAccountsResponse = {
  accounts: WhatsAppAccount[];
  connection: WhatsAppConnection;
};

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function WhatsAppAccountsPage() {
  const [provider, setProvider] = useState("meta");
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [status, setStatus] = useState<"active" | "disabled">("active");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [accounts, setAccounts] = useState<WhatsAppAccount[]>([]);
  const [connection, setConnection] = useState<WhatsAppConnection | null>(null);

  const providerLabel = useMemo(() => {
    if (provider === "meta") return "Meta (WhatsApp Cloud)";
    return provider;
  }, [provider]);

  const loadAccounts = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const response = await api.get<WhatsAppAccountsResponse>("/messaging/whatsapp-accounts");
      setAccounts(response.data.accounts ?? []);
      setConnection(response.data.connection ?? null);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to load WhatsApp connections");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void loadAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      setMessage(`Connected: ${providerLabel} • phone_number_id=${response.data.phone_number_id}`);
      setPhoneNumberId("");
      await loadAccounts();
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
        <h1 className="text-3xl font-semibold text-slate-900">Connect WhatsApp number</h1>
        <p className="mt-2 text-sm text-slate-500">
          Connect a WhatsApp Business number to this tenant so inbound messages and delivery callbacks route safely.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-slate-900">1) Find your Meta phone_number_id</h2>
            <p className="text-sm text-slate-500">
              <span className="font-medium text-slate-700">phone_number_id</span> is Meta&apos;s internal ID for your WhatsApp Business
              phone number. It&apos;s not the phone number itself (ex: <span className="font-mono">+351...</span>).
            </p>
            <p className="text-sm text-slate-500">
              Copy it from Meta / WhatsApp Manager (phone number details) and paste it below.
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">2) Connect</h2>
              <p className="text-sm text-slate-500">
                Routing key: <span className="font-mono">provider + phone_number_id</span>
              </p>
            </div>
            <Button type="button" variant="secondary" onClick={() => void loadAccounts()} disabled={refreshing}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
          </div>

          <form className="mt-4 space-y-4" onSubmit={onSubmit}>
            <div className="grid gap-2">
              <label className="text-sm text-slate-700" htmlFor="provider">Provider</label>
              <select
                id="provider"
                value={provider}
                onChange={(event) => setProvider(event.target.value)}
                className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900"
              >
                <option value="meta">Meta (WhatsApp Cloud)</option>
              </select>
              <p className="text-xs text-slate-500">
                This page supports the current provider-backed integration (WhatsApp Cloud / Graph API).
              </p>
            </div>

            <div className="grid gap-2">
              <label className="text-sm text-slate-700" htmlFor="phoneNumberId">Meta phone_number_id</label>
              <Input
                id="phoneNumberId"
                value={phoneNumberId}
                onChange={(event) => setPhoneNumberId(event.target.value)}
                placeholder="123456789012345"
                required
              />
              <p className="text-xs text-slate-500">
                Used to route Meta webhooks to the right tenant. You can connect multiple numbers per tenant.
              </p>
            </div>

            <div className="grid gap-2">
              <label className="text-sm text-slate-700" htmlFor="status">Connection status</label>
              <select
                id="status"
                value={status}
                onChange={(event) => setStatus(event.target.value as any)}
                className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900"
              >
                <option value="active">Active</option>
                <option value="disabled">Disabled</option>
              </select>
              <p className="text-xs text-slate-500">
                Status is stored with the mapping for admin visibility (routing is based on provider + phone_number_id).
              </p>
            </div>

            <Button type="submit" disabled={loading}>
              {loading ? "Connecting..." : "Connect WhatsApp number"}
            </Button>
          </form>
        </Card>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Connection health</h2>
            <p className="text-sm text-slate-500">Server readiness signals for this tenant.</p>
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-slate-200 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Webhook security</p>
            <p className="mt-1 text-sm text-slate-700">
              {connection?.webhook_secret_configured ? "Configured" : "Missing"} • <span className="font-mono">WHATSAPP_WEBHOOK_SECRET</span>
            </p>
          </div>
          <div className="rounded-md border border-slate-200 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Webhook verification</p>
            <p className="mt-1 text-sm text-slate-700">
              {connection?.webhook_verify_token_configured ? "Server ready" : "Missing"} •{" "}
              <span className="font-mono">WHATSAPP_WEBHOOK_VERIFY_TOKEN</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">Meta verification success is checked in Meta dashboard (not tracked here).</p>
          </div>
          <div className="rounded-md border border-slate-200 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Outbound provider</p>
            <p className="mt-1 text-sm text-slate-700">
              {connection?.cloud_access_token_configured ? "Enabled" : "Disabled"} •{" "}
              <span className="font-mono">WHATSAPP_CLOUD_ACCESS_TOKEN</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              API version: <span className="font-mono">{connection?.cloud_api_version ?? "—"}</span>
            </p>
          </div>
          <div className="rounded-md border border-slate-200 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Last delivery callback</p>
            <p className="mt-1 text-sm text-slate-700">
              {formatDateTime(connection?.last_delivery_callback_received_at)}
            </p>
            <p className="mt-1 text-xs text-slate-500">Based on stored delivery events (any connected number).</p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Connected numbers</h2>
            <p className="text-sm text-slate-500">Mappings that route Meta callbacks to this tenant.</p>
          </div>
        </div>

        {accounts.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No WhatsApp numbers connected yet.</p>
        ) : (
          <div className="mt-4 space-y-2">
            {accounts.map((acc) => (
              <div key={acc.id} className="flex flex-col gap-1 rounded-md border border-slate-200 p-3 md:flex-row md:items-center md:justify-between">
                <div className="text-sm text-slate-700">
                  <span className="font-medium">{acc.provider === "meta" ? "Meta" : acc.provider}</span>{" "}
                  <span className="text-slate-400">•</span>{" "}
                  <span className="font-mono">{acc.phone_number_id}</span>
                </div>
                <div className="flex flex-col gap-1 text-xs text-slate-500 md:flex-row md:items-center md:gap-3">
                  <span className={`rounded-full px-2 py-0.5 ${acc.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                    {acc.status}
                  </span>
                  <span>Connected: {formatDateTime(acc.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {message ? <p className="text-sm text-emerald-600">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
