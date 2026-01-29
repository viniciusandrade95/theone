import React from "react";

export function AppShell({
  children,
  header,
  sidebar,
}: {
  children: React.ReactNode;
  header: React.ReactNode;
  sidebar: React.ReactNode;
}) {
  return (
    <div style={styles.container}>
      <aside style={styles.sidebar}>{sidebar}</aside>
      <div style={styles.main}>
        <header style={styles.header}>{header}</header>
        <section style={styles.content}>{children}</section>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gridTemplateColumns: "260px 1fr",
    minHeight: "100vh",
    background: "#f8fafc",
  },
  sidebar: {
    background: "#0f172a",
    color: "white",
    padding: "2rem 1.5rem",
  },
  main: {
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "1.5rem 2rem",
    background: "white",
    borderBottom: "1px solid #e2e8f0",
  },
  content: {
    padding: "2rem",
  },
};
