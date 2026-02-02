"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "../../../../components/layout/AppShell";
import { Sidebar } from "../../../../components/layout/Sidebar";
import { TopBar } from "../../../../components/layout/TopBar";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Input } from "../../../../components/ui/input";
import { api } from "../../../../lib/api";

type Customer = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  tags: string[];
  stage: string;
  consent_marketing: boolean;
  created_at: string;
};

type Interaction = {
  id: string;
  type: string;
  content: string;
  created_at: string;
};

export default function CustomerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const customerId = params.customerId as string;

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadCustomer = async () => {
    setIsLoading(true);
    try {
      const [customerRes, interactionRes] = await Promise.all([
        api.get(`/crm/customers/${customerId}`),
        api.get(`/crm/customers/${customerId}/interactions`),
      ]);
      setCustomer(customerRes.data);
      setInteractions(interactionRes.data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load customer.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (customerId) {
      loadCustomer();
    }
  }, [customerId]);

  const handleAddInteraction = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!note.trim()) {
      return;
    }
    setError(null);
    try {
      await api.post(`/crm/customers/${customerId}/interactions`, {
        type: "note",
        content: note.trim(),
      });
      setNote("");
      await loadCustomer();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to add interaction.");
    }
  };

  if (isLoading && !customer) {
    return (
      <AppShell header={<TopBar />} sidebar={<Sidebar />}>
        <p className="text-sm text-slate-500">Loading customer...</p>
      </AppShell>
    );
  }

  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          ← Back to customers
        </Button>

        {customer ? (
          <Card>
            <CardHeader>
              <CardTitle>{customer.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-600">
              <p>
                <span className="font-semibold text-slate-700">Email:</span>{" "}
                {customer.email ?? "Not provided"}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Phone:</span>{" "}
                {customer.phone ?? "Not provided"}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Stage:</span> {customer.stage}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Tags:</span>{" "}
                {customer.tags.length ? customer.tags.join(", ") : "None"}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Created:</span> {customer.created_at}
              </p>
              <p>
                <span className="font-semibold text-slate-700">Marketing consent:</span>{" "}
                {customer.consent_marketing ? "Yes" : "No"}
              </p>
              <Link href={`/dashboard/customers/${customer.id}`} className="text-xs text-slate-400">
                ID: {customer.id}
              </Link>
            </CardContent>
          </Card>
        ) : (
          <p className="text-sm text-slate-500">Customer not found.</p>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Interactions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {interactions.length === 0 ? (
              <p className="text-sm text-slate-500">No interactions yet.</p>
            ) : (
              <ul className="space-y-3">
                {interactions.map((interaction) => (
                  <li key={interaction.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="font-semibold uppercase">{interaction.type}</span>
                      <span>{interaction.created_at}</span>
                    </div>
                    <p className="mt-2 text-slate-700">{interaction.content}</p>
                  </li>
                ))}
              </ul>
            )}

            <form onSubmit={handleAddInteraction} className="space-y-3">
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Add note
                <Input
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder="Capture the latest touchpoint..."
                />
              </label>
              {error ? (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                  {error}
                </div>
              ) : null}
              <Button type="submit">Add interaction</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
