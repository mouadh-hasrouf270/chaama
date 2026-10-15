import type { LucideIcon } from "lucide-react";
import { Card } from "./Card";

export function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
}) {
  return (
    <Card className="flex items-start justify-between p-5">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-chaama-muted">
          {label}
        </p>
        <p className="mt-2 font-display text-[28px] text-chaama-text">{value}</p>
      </div>
      <Icon size={20} strokeWidth={1.6} className="text-chaama-gold" />
    </Card>
  );
}
