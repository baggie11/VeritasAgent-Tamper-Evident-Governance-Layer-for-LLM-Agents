"use client";

import { clsx } from "clsx";

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={clsx("rounded-xl border border-zinc-300 bg-card p-4 shadow-sm", className)}>{children}</div>;
}

export function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={clsx("rounded-full px-2 py-1 text-xs font-semibold", ok ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800")}>
      {label}
    </span>
  );
}
