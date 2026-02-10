"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-errors";
import { setAuthToken, setTenantId } from "@/lib/auth";
import { appPath } from "@/lib/paths";

type Workspace = {
  tenant_id: string;
  tenant_name: string;
};

type LoginEmailResponse =
  | {
      mode: "authenticated";
      auth: {
        user_id: string;
        tenant_id: string;
        email: string;
        token: string;
      };
      preauth_token: null;
      workspaces: null;
    }
  | {
      mode: "select_workspace";
      auth: null;
      preauth_token: string;
      workspaces: Workspace[];
    };

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [preauthToken, setPreauthToken] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null);
  const [selectedTenantId, setSelectedTenantId] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isWorkspaceStep = useMemo(
    () => !!preauthToken && !!workspaces,
    [preauthToken, workspaces],
  );

  async function onSubmitEmailPassword(e: React.FormEvent) {
    e.preventDefault(); // 🔴 THIS WAS MISSING

    setError(null);
    setLoading(true);

    console.log("LOGIN CLICKED", email, password);

    try {
      const resp = await api.post<LoginEmailResponse>(
        "/auth/login_email",
        { email, password },
      );

      const data = resp.data;

      if (data.mode === "authenticated" && data.auth) {
        setAuthToken(data.auth.token);
        setTenantId(data.auth.tenant_id);
        router.push(appPath("/dashboard"));
        return;
      }

      if (data.mode === "select_workspace") {
        setPreauthToken(data.preauth_token);
        setWorkspaces(data.workspaces || []);
        setSelectedTenantId(
          data.workspaces?.[0]?.tenant_id || "",
        );
        return;
      }

      setError("Unexpected login response.");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Login failed."));
    } finally {
      setLoading(false);
    }
  }

  async function onContinueWorkspace() {
    if (!preauthToken || !selectedTenantId) {
      setError("Please select a workspace.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const resp = await api.post("/auth/select_workspace", {
        preauth_token: preauthToken,
        tenant_id: selectedTenantId,
      });

      const auth = resp.data as {
        user_id: string;
        tenant_id: string;
        email: string;
        token: string;
      };

      setAuthToken(auth.token);
      setTenantId(auth.tenant_id);
      router.push(appPath("/dashboard"));
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Workspace selection failed."));
    } finally {
      setLoading(false);
    }
  }

  function onBack() {
    setError(null);
    setPreauthToken(null);
    setWorkspaces(null);
    setSelectedTenantId("");
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">
            {isWorkspaceStep ? "Choose a workspace" : "Welcome back"}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            {isWorkspaceStep
              ? "Select which workspace you want to access."
              : "Log in with your email and password."}
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {!isWorkspaceStep && (
          <form
            onSubmit={onSubmitEmailPassword}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                type="password"
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Logging in..." : "Log in"}
            </button>

            <div className="text-sm text-slate-600 text-center">
              Don&apos;t have an account?{" "}
              <a
                className="font-medium text-slate-900 hover:underline"
                href="/register"
              >
                Create one
              </a>
            </div>
          </form>
        )}

        {isWorkspaceStep && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Workspace
              </label>
              <select
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
                value={selectedTenantId}
                onChange={(e) =>
                  setSelectedTenantId(e.target.value)
                }
              >
                {workspaces?.map((w) => (
                  <option key={w.tenant_id} value={w.tenant_id}>
                    {w.tenant_name}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={onContinueWorkspace}
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Continuing..." : "Continue"}
            </button>

            <button
              type="button"
              onClick={onBack}
              disabled={loading}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 hover:bg-slate-50 disabled:opacity-60"
            >
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
