import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-chaama-gold">
          {eyebrow}
        </p>
        <h1 className="font-display text-[32px] leading-tight tracking-[-0.8px] text-chaama-text sm:text-[36px]">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2 text-[14px] text-chaama-muted">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`border border-chaama-border bg-white ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  className = "",
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  className?: string;
}) {
  return (
    <div
      className={`flex h-full min-h-0 w-full flex-col justify-between rounded-2xl border border-chaama-border bg-white p-5 transition-shadow group-hover:shadow-sm ${className}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[12px] font-medium text-chaama-muted">{label}</p>

          <p className="mt-2 text-3xl font-semibold tracking-tight text-chaama-dark">
            {value}
          </p>
        </div>

        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-chaama-green text-chaama-dark">
          <Icon size={19} strokeWidth={1.8} />
        </div>
      </div>
    </div>
  );
}
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
