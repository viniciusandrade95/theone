import { AppShell } from "../../components/layout/AppShell";
import { Sidebar } from "../../components/layout/Sidebar";
import { TopBar } from "../../components/layout/TopBar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function DashboardPage() {
  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <section className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Your workspace is ready</CardTitle>
            <CardDescription>
              This is the foundation for your CRM, analytics, and messaging UI. Next up:
              customers, interactions, and dashboards.
            </CardDescription>
          </CardHeader>
        </Card>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              title: "CRM",
              body: "Customer profiles and interaction history.",
            },
            {
              title: "Analytics",
              body: "KPIs, growth charts, and insights.",
            },
            {
              title: "Messaging",
              body: "Unified inbox for inbound conversations.",
            },
          ].map((card) => (
            <Card key={card.title}>
              <CardHeader>
                <CardTitle>{card.title}</CardTitle>
                <CardDescription>{card.body}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-500">
                  Planned for Phase 2-3. Placeholder to align with enterprise roadmap.
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
