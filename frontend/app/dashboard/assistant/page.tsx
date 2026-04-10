"use client";

import { FormEvent, useMemo, useState } from "react";

import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { api } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-errors";

type AssistantReply = {
  conversation_id: string;
  session_id: string | null;
  status: string;
  trace_id?: string;
  reply?: {
    text?: string;
    actions?: Array<{ label?: string; type?: string; payload?: unknown }>;
  };
  handoff?: {
    requested: boolean;
    reason?: string | null;
  };
};

export default function AssistantPage() {
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const canSend = useMemo(() => message.trim().length > 0 && !busy, [message, busy]);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSend) return;
    setBusy(true);
    setError(null);
    try {
      const resp = await api.post<AssistantReply>("/api/chatbot/message", {
        message,
        conversation_id: conversationId,
        session_id: sessionId,
        surface: "dashboard",
      });
      setReply(resp.data);
      setConversationId(resp.data.conversation_id ?? null);
      setSessionId(resp.data.session_id ?? null);
      setMessage("");
    } catch (err) {
      setError(getApiErrorMessage(err as unknown, "Unable to reach assistant."));
    } finally {
      setBusy(false);
    }
  };

  const resetConversation = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/chatbot/reset", {
        conversation_id: conversationId,
        surface: "dashboard",
      });
      setConversationId(null);
      setSessionId(null);
      setReply(null);
    } catch (err) {
      setError(getApiErrorMessage(err as unknown, "Unable to reset conversation."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-4">
        <h1 className="text-2xl font-semibold text-slate-900">Assistant</h1>
        <p className="text-sm text-slate-500">Internal assistant proxy (theone -&gt; chatbot1).</p>
      </div>
      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
        <form onSubmit={sendMessage} className="space-y-3">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask the assistant about customers, appointments, or booking settings..."
            className="min-h-28 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="flex gap-2">
            <button disabled={!canSend} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
              {busy ? "Sending..." : "Send"}
            </button>
            <button type="button" onClick={resetConversation} disabled={busy} className="rounded-xl border border-slate-300 px-4 py-2 text-sm">
              Reset conversation
            </button>
          </div>
        </form>

        <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
          <p>conversation_id: {conversationId ?? "-"}</p>
          <p>session_id: {sessionId ?? "-"}</p>
          <p>trace_id: {reply?.trace_id ?? "-"}</p>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {reply ? (
          <div className="space-y-2 rounded-xl border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-900">Assistant reply</p>
            <p className="text-sm text-slate-700">{reply.reply?.text || "(empty response)"}</p>
            {reply.handoff?.requested ? (
              <p className="text-xs font-medium text-amber-700">Handoff requested{reply.handoff.reason ? `: ${reply.handoff.reason}` : ""}</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </DashboardLayout>
  );
}
