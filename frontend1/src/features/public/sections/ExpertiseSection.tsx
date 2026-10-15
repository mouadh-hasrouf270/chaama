import useApi from "../../../hooks/useApi";
import {
  Building2,
  FileText,
  Gavel,
  Landmark,
  Scale,
  Users,
} from "lucide-react";

const icons = [Building2, Scale, FileText, Gavel, Landmark, Users];

export default function ExpertiseSection() {
  const { data, loading, error } = useApi("/v1/public/practice-areas/", true);
  const expertises = (data || []).map((area: any, index: number) => ({
    icon: icons[index % icons.length], title: area.name, desc: area.description,
  }));
  return (
    <section
      id="expertises"
      className="bg-[var(--chaama-green)] px-6 py-24 lg:px-10 lg:py-32"
    >
      <div className="mx-auto max-w-[1200px]">
        {/* HEADER */}
        <div className="mb-14 max-w-2xl">
          <p className="mb-5 flex items-center gap-3 text-[9px] font-semibold uppercase tracking-[0.3em] text-[var(--chaama-gold)]">
            <span className="h-px w-8 bg-[var(--chaama-gold)]" />
            Nos expertises
          </p>

          <h2 className="font-display text-[clamp(34px,4.5vw,56px)] leading-[0.95] tracking-[-0.04em] text-[var(--chaama-dark)]">
            Une expertise au service
            <br />
            <em className="font-medium text-[var(--chaama-gold)]">
              de vos enjeux.
            </em>
          </h2>
        </div>

        {loading && <p role="status">Chargement…</p>}
        {error && <p role="alert">{error}</p>}
        {!loading && !error && !expertises.length && <p>Aucune expertise publiée.</p>}
        {/* CARDS */}
        <div className="grid gap-px overflow-hidden bg-[var(--chaama-border)] sm:grid-cols-2 lg:grid-cols-3">
          {expertises.map((expertise) => {
            const Icon = expertise.icon;

            return (
              <div
                key={expertise.title}
                className="group relative bg-[var(--chaama-cream)] p-8 transition-all duration-300 hover:bg-[var(--chaama-green)]"
              >
                {/* ICON */}
                <div className="mb-7 flex h-11 w-11 items-center justify-center bg-[var(--chaama-green)] text-[var(--chaama-dark)] transition-all duration-300 group-hover:bg-[var(--chaama-gold)] group-hover:text-[var(--chaama-cream)]">
                  <Icon size={20} strokeWidth={1.5} />
                </div>

                {/* TITLE */}
                <h3 className="mb-3 font-display text-xl text-[var(--chaama-dark)]">
                  {expertise.title}
                </h3>

                {/* DESCRIPTION */}
                <p className="text-[13px] leading-[1.8] text-[var(--chaama-muted)]">
                  {expertise.desc}
                </p>

                {/* DECORATIVE LINE */}
                <div className="mt-7 h-px w-0 bg-[var(--chaama-gold)] transition-all duration-500 group-hover:w-10" />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
