"use client";

import { useState } from "react";
import { AppShell } from "../../../components/layout/AppShell";
import { Sidebar } from "../../../components/layout/Sidebar";
import { TopBar } from "../../../components/layout/TopBar";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { useTenant } from "../../../lib/tenant";

export default function SettingsPage() {
  const { tenantId, updateTenant } = useTenant();
  const [draftTenantId, setDraftTenantId] = useState(tenantId);

  const handleSave = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateTenant(draftTenantId.trim());
  };

  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Tenant settings</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Active tenant ID
                <Input
                  value={draftTenantId}
                  onChange={(event) => setDraftTenantId(event.target.value)}
                  placeholder="tenant-id"
                />
              </label>
              <Button type="submit">Update tenant</Button>
            </form>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Profile (coming soon)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500">
              Profile settings, API keys, and webhooks will be available in Phase 4.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
