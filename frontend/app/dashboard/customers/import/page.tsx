"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { appPath } from "@/lib/paths";

export default function ImportCustomersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Import customers</h1>
        <p className="text-sm text-slate-500">This MVP does not include CSV import yet.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Coming soon</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-600">
          <p>
            For now, you can create customers manually. We will add a simple import flow in a follow-up PR.
          </p>
          <Link
            href={appPath("/dashboard/customers/new")}
            className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition hover:border-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
          >
            Create customer
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
