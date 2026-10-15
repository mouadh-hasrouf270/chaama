import { Check } from "lucide-react";

interface SelectableCardProps {
  title: string;
  subtitle?: string;
  selected: boolean;
  onSelect: () => void;
  indicator?: "dot" | "check";
}

export default function SelectableCard({
  title,
  subtitle,
  selected,
  onSelect,
  indicator = "dot",
}: SelectableCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`flex w-full items-center justify-between gap-4 border px-5 py-4 text-left transition-colors ${
        selected
          ? "border-ink/25 bg-sage"
          : "border-ink/10 bg-transparent hover:border-ink/25"
      }`}
    >
      <span className="flex items-center gap-3">
        {indicator === "dot" && (
          <span
            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
              selected ? "border-navy" : "border-ink/30"
            }`}
          >
            {selected && <span className="h-2 w-2 rounded-full bg-navy" />}
          </span>
        )}
        <span>
          <span className="block text-sm font-semibold text-ink">{title}</span>
          {subtitle && (
            <span className="mt-0.5 block text-sm text-ink-muted">
              {subtitle}
            </span>
          )}
        </span>
      </span>

      {indicator === "check" && (
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
            selected
              ? "border-navy bg-navy text-cream"
              : "border-ink/20 text-transparent"
          }`}
        >
          <Check size={14} />
        </span>
      )}
    </button>
  );
}
