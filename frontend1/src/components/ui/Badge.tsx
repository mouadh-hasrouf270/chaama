import type { ReactNode } from "react";

type BadgeTone = "gold" | "muted" | "green" | "alert";

const badgeTones: Record<BadgeTone, string> = {
  gold: "bg-chaama-gold/10 text-chaama-dark2 border-chaama-gold/30",
  muted: "bg-chaama-border/40 text-chaama-muted border-chaama-border",
  green: "bg-chaama-green text-chaama-dark border-chaama-green",
  alert: "bg-red-50 text-red-700 border-red-200",
};

export function Badge({
  tone = "muted",
  children,
}: {
  tone?: BadgeTone;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center border px-2.5 py-1 text-[11px] font-semibold ${badgeTones[tone]}`}
    >
      {children}
    </span>
  );
}
