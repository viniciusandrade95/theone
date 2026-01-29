import React from "react";

export function TopBar() {
  return (
    <div style={styles.container}>
      <div>
        <p style={styles.title}>Dashboard</p>
        <p style={styles.subtitle}>Welcome back to your workspace.</p>
      </div>
      <div style={styles.profile}>
        <span style={styles.avatar}>BC</span>
        <div>
          <p style={styles.name}>Beauty CRM</p>
          <p style={styles.role}>Admin</p>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
  },
  title: {
    margin: 0,
    fontSize: "1.25rem",
    fontWeight: 700,
  },
  subtitle: {
    margin: 0,
    color: "#64748b",
  },
  profile: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  avatar: {
    width: "40px",
    height: "40px",
    borderRadius: "999px",
    background: "#1e293b",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
  },
  name: {
    margin: 0,
    fontWeight: 600,
  },
  role: {
    margin: 0,
    color: "#94a3b8",
    fontSize: "0.85rem",
  },
};
