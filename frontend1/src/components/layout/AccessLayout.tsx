import type { ReactNode } from "react";
import { ArrowLeft } from "lucide-react";

type AccessLayoutProps = {
  eyebrow: string;
  title: ReactNode;
  description: string;
  children: ReactNode;
  onBack?: () => void;
};

export function AccessLayout({
  eyebrow,
  title,
  description,
  children,
  onBack,
}: AccessLayoutProps) {
  return (
    <main className="min-h-screen bg-chaama-cream text-chaama-text">
      <div className="grid min-h-screen lg:grid-cols-[minmax(320px,38%)_1fr]">
        {/* LEFT — dark panel */}
        <aside className="relative hidden overflow-hidden bg-chaama-dark px-10 py-9 text-chaama-cream lg:flex lg:min-h-screen lg:flex-col xl:px-16">
          {/* Content — TOP */}
          <div className="relative z-10 mt-20 max-w-[380px] pt-5">
            <p className="mb-6 text-[10px] font-semibold uppercase tracking-[0.3em] text-chaama-gold">
              {eyebrow}
            </p>

            <h1 className="font-display text-[46px] leading-[1.04] tracking-[-1.8px] text-chaama-cream xl:text-[56px]">
              {title}
            </h1>

            <p className="mt-7 max-w-[330px] text-[14px] leading-7 text-chaama-cream/60">
              {description}
            </p>
          </div>

          {/* Footer */}
          <p className="relative z-10 mt-auto text-[9px] font-semibold uppercase tracking-[0.26em] text-chaama-muted">
            Espace professionnel · 2026
          </p>

          {/* Decorative circles */}
          <div className="absolute -right-28 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full border border-chaama-gold/10" />

          <div className="absolute -right-12 top-1/2 h-40 w-40 -translate-y-1/2 rounded-full border border-chaama-gold/10" />
        </aside>

        {/* RIGHT — form area */}
        <section className="flex min-h-screen flex-col px-6 py-8 sm:px-12 sm:py-12 lg:px-16 lg:py-16 xl:px-24">
          <div className="flex items-center justify-between lg:justify-end">
            <div className="flex items-center gap-3 lg:hidden">
              <div className="flex h-8 w-8 items-center justify-center border border-chaama-gold font-display text-lg text-chaama-gold">
                C
              </div>
              <span className="text-[10px] font-medium uppercase tracking-[0.3em] text-chaama-dark">
                CHAAMA
              </span>
            </div>
            <span className="text-[9px] font-semibold uppercase tracking-[0.25em] text-chaama-muted pt-7">
              Accès sécurisé
            </span>
          </div>
          <div className="flex flex-1 items-center justify-center py-12">
            <div className="w-full max-w-[520px] animate-rise">{children}</div>
          </div>
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="mx-auto flex items-center gap-2 text-[11px] font-semibold text-chaama-dark transition-opacity hover:opacity-60 cursor-pointer"
            >
              <ArrowLeft size={14} strokeWidth={1.8} /> Retour à la connexion
            </button>
          )}
        </section>
      </div>
    </main>
  );
}

export function Field({
  label,
  type = "text",
  placeholder,
  value,
  onChange,
}: {
  label: string;
  type?: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
        {label}
      </span>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-[56px] w-full border border-chaama-border bg-chaama-cream px-5 text-[15px] text-chaama-text outline-none transition placeholder:text-chaama-muted/50 focus:border-chaama-gold focus:ring-2 focus:ring-chaama-gold/20"
      />
    </label>
  );
}

export function GoldButton({
  children,
  disabled = false,
  onClick,
  type = "submit",
}: {
  children: ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className="mt-7 h-[54px] w-full bg-chaama-dark text-[14px] font-semibold text-white transition hover:bg-chaama-dark2 disabled:hover:bg-chaama-dark disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}
