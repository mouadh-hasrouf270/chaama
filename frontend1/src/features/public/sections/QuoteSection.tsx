import { Quote } from "lucide-react";

export default function QuoteSection() {
  return (
    <section className="relative overflow-hidden bg-teal-800 px-6 py-24 lg:px-10 lg:py-32">
      <div
        className="absolute inset-0 bg-cover bg-center opacity-10"
        style={{
          backgroundImage:
            "url(https://images.pexels.com/photos/8112201/pexels-photo-8112201.jpeg?auto=compress&cs=tinysrgb&w=1920)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-3xl text-center">
        <Quote size={40} className="mx-auto mb-8 text-gold-400/60" />

        <p className="font-serif text-[clamp(24px,3vw,38px)] leading-[1.35] tracking-tight text-white">
          « La justice est la constante et perpétuelle volonté de rendre à
          chacun ce qui lui appartient. »
        </p>

        <p className="mt-8 text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-300">
          — Ulpien, juriste romain
        </p>
      </div>
    </section>
  );
}
