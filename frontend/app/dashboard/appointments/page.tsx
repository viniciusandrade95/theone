"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Customer = { id: string; name: string };
type Service = { id: string; name: string; duration_minutes: number };

type Appointment = {
  id: string;
  customer_id: string;
  service_id: string | null;
  starts_at: string;
  ends_at: string;
  status: string;
  notes: string | null;
};

export default function AppointmentsPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [items, setItems] = useState<Appointment[]>([]);

  const [customerId, setCustomerId] = useState("");
  const [serviceId, setServiceId] = useState<string | "">("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [notes, setNotes] = useState("");

  async function load() {
    const [c, s, a] = await Promise.all([
      api.get<Customer[]>("/crm/customers"),
      api.get<Service[]>("/crm/services"),
      api.get<Appointment[]>("/crm/appointments"),
    ]);
    setCustomers(c.data);
    setServices(s.data);
    setItems(a.data);
  }

  useEffect(() => {
    load();
  }, []);

  async function create() {
    await api.post("/crm/appointments", {
      customer_id: customerId,
      service_id: serviceId || null,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
      status: "booked",
      notes: notes || null,
    });
    setNotes("");
    await load();
  }

  async function remove(id: string) {
    await api.delete(`/crm/appointments/${id}`);
    await load();
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        <div className="text-lg font-semibold text-slate-900">Appointments</div>

        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-5">
          <select className="rounded-xl border px-3 py-2" value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
            <option value="">Select customer</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <select className="rounded-xl border px-3 py-2" value={serviceId} onChange={(e) => setServiceId(e.target.value)}>
            <option value="">No service</option>
            {services.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>

          <input className="rounded-xl border px-3 py-2" type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} />
          <input className="rounded-xl border px-3 py-2" type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} />

          <button
            disabled={!customerId || !startsAt || !endsAt}
            onClick={create}
            className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60"
          >
            Book
          </button>
        </div>

        <input className="mt-3 w-full rounded-xl border px-3 py-2" placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>

      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        <div className="text-sm text-slate-600 mb-3">{items.length} appointments</div>
        <div className="divide-y">
          {items.map((a) => (
            <div key={a.id} className="py-3 flex items-center justify-between">
              <div className="text-sm">
                <div className="font-medium text-slate-900">
                  {a.customer_id} {a.service_id ? `• service ${a.service_id}` : ""}
                </div>
                <div className="text-slate-600">
                  {new Date(a.starts_at).toLocaleString()} → {new Date(a.ends_at).toLocaleString()} • {a.status}
                </div>
              </div>
              <button onClick={() => remove(a.id)} className="rounded-xl border px-3 py-2 text-sm font-semibold hover:bg-slate-50">
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
