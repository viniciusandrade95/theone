"use client";

import Link from "next/link";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type TrendTone = "neutral" | "positive" | "warning" | "negative";

type TrendPill = {
  label: string;
  tone?: TrendTone;
};

export function TrendMiniCard({
  title,
  value,
  description,
  pill,
  href,
  className,
}: {
  title: string;
  value: React.ReactNode;
  description?: string;
  pill?: TrendPill;
  href?: string;
  className?: string;
}) {
  const tone = pill?.tone ?? "neutral";
  const pillClass =
    tone === "positive"
      ? "bg-emerald-50 text-emerald-700"
      : tone === "warning"
        ? "bg-amber-50 text-amber-700"
        : tone === "negative"
          ? "bg-rose-50 text-rose-700"
          : "bg-slate-100 text-slate-700";

  const content = (
    <Card
      className={cn(
        "group relative p-4 transition-colors",
        href ? "hover:border-slate-300" : "",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
        {pill ? (
          <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold", pillClass)}>{pill.label}</span>
        ) : null}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
      {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
    </Card>
  );

  if (!href) {
    return content;
  }

  return (
    <Link
      href={href}
      className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
    >
      {content}
    </Link>
  );
}

