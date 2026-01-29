import { AppShell } from "../../../components/layout/AppShell";
import { Sidebar } from "../../../components/layout/Sidebar";
import { TopBar } from "../../../components/layout/TopBar";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";

export default function AnalyticsPage() {
  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <Card>
        <CardHeader>
          <CardTitle>Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            KPI widgets and charts are scheduled for Phase 3. This placeholder ensures
            analytics navigation is live in Phase 1.
          </p>
        </CardContent>
      </Card>
    </AppShell>
  );
}
