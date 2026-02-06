"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Service = {
  id: string;
  name: string;
  price_cents: number;
  duration_minutes: number;
};

export default function ServicesPage() {
  const [items, setItems] = useState<Service[]>([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState(0);
  const [duration, setDuration] = useState(30);
  const [loading, setLoading] = useState(false);

  async function load() {
    const resp = await api.get<Service[]>("/crm/services");
    setItems(resp.data);
  }

  useEffect(() => {
    load();
  }, []);

  async function create() {
    setLoading(true);
    try {
      await api.post("/crm/services", {
        name,
        price_cents: price,
        duration_minutes: duration,
      });
      setName("");
      setPrice(0);
      setDuration(30);
      await load();
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: string) {
    await api.delete(`/crm/services/${id}`);
    await load();
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        <div className="text-lg font-semibold text-slate-900">Services</div>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4">
          <input className="rounded-xl border px-3 py-2" placeholder="Service name" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="rounded-xl border px-3 py-2" type="number" placeholder="Price cents" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
          <input className="rounded-xl border px-3 py-2" type="number" placeholder="Duration minutes" value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
          <button disabled={loading} onClick={create} className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
            Add
          </button>
        </div>
      </div>

      <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200">
        <div className="text-sm text-slate-600 mb-3">{items.length} services</div>
        <div className="divide-y">
          {items.map((s) => (
            <div key={s.id} className="py-3 flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900">{s.name}</div>
                <div className="text-sm text-slate-600">
                  €{(s.price_cents / 100).toFixed(2)} • {s.duration_minutes} min
                </div>
              </div>
              <button onClick={() => remove(s.id)} className="rounded-xl border px-3 py-2 text-sm font-semibold hover:bg-slate-50">
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
