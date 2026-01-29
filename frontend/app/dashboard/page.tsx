import { AppShell } from "../../components/layout/AppShell";
import { Sidebar } from "../../components/layout/Sidebar";
import { TopBar } from "../../components/layout/TopBar";

export default function DashboardPage() {
  return (
    <AppShell header={<TopBar />} sidebar={<Sidebar />}>
      <section style={styles.hero}>
        <h1 style={styles.title}>Your workspace is ready</h1>
        <p style={styles.subtitle}>
          This is the foundation for your CRM, analytics, and messaging UI.
          Next up: customers, interactions, and dashboards.
        </p>
        <div style={styles.cards}>
          <div style={styles.card}>
            <p style={styles.cardTitle}>CRM</p>
            <p style={styles.cardBody}>Customer profiles and interaction history.</p>
          </div>
          <div style={styles.card}>
            <p style={styles.cardTitle}>Analytics</p>
            <p style={styles.cardBody}>KPIs, growth charts, and insights.</p>
          </div>
          <div style={styles.card}>
            <p style={styles.cardTitle}>Messaging</p>
            <p style={styles.cardBody}>Unified inbox for inbound conversations.</p>
          </div>
        </div>
      </section>
    </AppShell>
  );
}

const styles: Record<string, React.CSSProperties> = {
  hero: {
    background: "white",
    borderRadius: "16px",
    padding: "2rem",
    boxShadow: "0 12px 30px rgba(15, 23, 42, 0.08)",
  },
  title: {
    margin: 0,
    fontSize: "1.8rem",
    fontWeight: 700,
  },
  subtitle: {
    marginTop: "0.75rem",
    color: "#64748b",
  },
  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "1rem",
    marginTop: "2rem",
  },
  card: {
    padding: "1.5rem",
    borderRadius: "14px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
  },
  cardTitle: {
    margin: 0,
    fontWeight: 700,
  },
  cardBody: {
    margin: "0.5rem 0 0",
    color: "#64748b",
  },
};
