import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-white to-slate-50 px-6 py-12">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-semibold text-slate-900">Beauty CRM</h1>
        <p className="mt-2 text-sm text-slate-600">
          Log in to access your dashboard, customers, appointments, booking, and outbound messaging.
        </p>

        <div className="mt-6 flex flex-wrap gap-2">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition hover:border-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
          >
            Create account
          </Link>
        </div>

        <p className="mt-6 text-xs text-slate-500">
          If login fails on Render, ensure the frontend env var `NEXT_PUBLIC_API_BASE_URL` points to the API service URL
          and the API `CORS_ALLOW_ORIGINS` includes this frontend URL.
        </p>
      </div>
    </main>
  );
}
