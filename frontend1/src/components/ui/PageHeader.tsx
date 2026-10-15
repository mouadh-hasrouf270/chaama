import type { ReactNode } from "react";

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
