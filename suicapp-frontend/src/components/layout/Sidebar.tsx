import React from "react";

const navItems = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Customers", href: "/dashboard/customers" },
  { label: "Analytics", href: "/dashboard/analytics" },
  { label: "Settings", href: "/dashboard/settings" },
];

export function Sidebar() {
  return (
    <div>
      <h2 style={styles.brand}>Beauty CRM</h2>
      <nav style={styles.nav}>
        {navItems.map((item) => (
          <a key={item.href} href={item.href} style={styles.link}>
            {item.label}
          </a>
        ))}
      </nav>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  brand: {
    margin: 0,
    fontSize: "1.25rem",
    fontWeight: 700,
  },
  nav: {
    marginTop: "2rem",
    display: "grid",
    gap: "0.75rem",
  },
  link: {
    color: "#e2e8f0",
    textDecoration: "none",
    fontSize: "0.95rem",
  },
};
