"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      }, {
        headers: {
          "X-Tenant-ID": tenantId,
        },
      });

      const token = response.data?.token;
      if (!token) {
        throw new Error("Missing auth token in response.");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("tenant_id", tenantId);
      document.cookie = `token=${token}; path=/`;
      router.push("/dashboard");
    } catch (loginError) {
      const message =
        loginError instanceof Error
          ? loginError.message
          : "Login failed. Please try again.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <h1 style={styles.title}>Welcome back</h1>
        <p style={styles.subtitle}>Sign in to your Beauty CRM workspace.</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Tenant ID
            <input
              style={styles.input}
              value={tenantId}
              onChange={(event) => setTenantId(event.target.value)}
              placeholder="e.g. 9b0f..."
              required
            />
          </label>
          <label style={styles.label}>
            Email
            <input
              style={styles.input}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              placeholder="you@company.com"
              required
            />
          </label>
          <label style={styles.label}>
            Password
            <input
              style={styles.input}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              placeholder="••••••••"
              required
            />
          </label>
          {error ? <p style={styles.error}>{error}</p> : null}
          <button type="submit" style={styles.button} disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "2rem",
    background: "linear-gradient(135deg, #e2e8f0, #f8fafc)",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    background: "white",
    borderRadius: "16px",
    padding: "2.5rem",
    boxShadow: "0 25px 60px rgba(15, 23, 42, 0.12)",
  },
  title: {
    margin: 0,
    fontSize: "1.75rem",
    fontWeight: 700,
  },
  subtitle: {
    margin: "0.5rem 0 2rem",
    color: "#64748b",
  },
  form: {
    display: "grid",
    gap: "1rem",
  },
  label: {
    display: "grid",
    gap: "0.5rem",
    fontWeight: 600,
    color: "#1e293b",
  },
  input: {
    padding: "0.75rem 0.9rem",
    borderRadius: "10px",
    border: "1px solid #cbd5f5",
    fontSize: "0.95rem",
  },
  button: {
    padding: "0.9rem",
    borderRadius: "10px",
    border: "none",
    background: "#2563eb",
    color: "white",
    fontWeight: 600,
    cursor: "pointer",
  },
  error: {
    margin: 0,
    color: "#dc2626",
    fontWeight: 600,
  },
};
