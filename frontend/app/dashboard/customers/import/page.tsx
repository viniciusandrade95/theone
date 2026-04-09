"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
          <Button asChild variant="secondary">
            <Link href={appPath("/dashboard/customers/new")}>Create customer</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

