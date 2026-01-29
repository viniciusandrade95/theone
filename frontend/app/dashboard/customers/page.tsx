import { AppShell } from "../../../components/layout/AppShell";
import { Sidebar } from "../../../components/layout/Sidebar";
import { TopBar } from "../../../components/layout/TopBar";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";

export default function CustomersPage() {
  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <Card>
        <CardHeader>
          <CardTitle>Customers</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            Customer list, filters, and profiles are scheduled for Phase 2. This
            placeholder keeps navigation consistent during Phase 1.
          </p>
        </CardContent>
      </Card>
    </AppShell>
  );
}
