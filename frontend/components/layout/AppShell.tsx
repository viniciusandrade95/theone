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
    <div className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="hidden bg-slate-950 px-6 py-8 text-white lg:block">
        {sidebar}
      </aside>
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5 shadow-sm">
          {header}
        </header>
        <section className="flex-1 px-6 py-8">{children}</section>
      </div>
    </div>
  );
}
