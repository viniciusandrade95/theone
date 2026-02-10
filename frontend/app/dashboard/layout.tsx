import RequireAuth from "@/components/RequireAuth";
import { DashboardLayout as DashboardAppLayout } from "@/components/dashboard/DashboardLayout";
import { DefaultLocationProvider } from "@/lib/default-location";

export default function DashboardRouteLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <DefaultLocationProvider>
        <DashboardAppLayout>{children}</DashboardAppLayout>
      </DefaultLocationProvider>
    </RequireAuth>
  );
}
