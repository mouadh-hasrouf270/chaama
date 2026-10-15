import { Mail, Phone, MapPin } from "lucide-react";
import { Link } from "react-router-dom";

const ContactSection = () => {
  return (
    <section id="contact" className="bg-[#e5ece7] py-24 lg:py-24">
      <div className="container-chaama">
        <div className="grid gap-12 lg:grid-cols-[1.3fr_0.7fr]">
          <div>
            <div className="mb-5 flex items-center gap-3">
              <div className="h-px w-10 bg-[#193a42]/40" />

              <span className="text-[9px] uppercase tracking-[0.3em]">
                Contact
              </span>
            </div>

            <h2 className="font-display text-4xl sm:text-5xl">
              Parlons de ce qui vous
              <br />
              amène ici.
            </h2>

            <p className="mt-6 max-w-xl text-sm leading-6 text-[#718087]">
              Un premier message suffit. Nous vous répondrons avec discrétion et
              vous indiquerons la meilleure manière d'avancer.
            </p>

            <Link
              to="/contact"
              className="mt-7 inline-block text-xs underline underline-offset-4"
            >
              Écrire au cabinet →
            </Link>
          </div>

          <div className="border-l border-[#193a42]/10 pl-8"><p className="mb-5 text-xs text-amber-800">Coordonnées de démonstration — à remplacer avant publication.</p>
            <div className="mb-7 flex gap-4">
              <Mail size={17} strokeWidth={1.3} />

              <div>
                <p className="text-[9px] uppercase tracking-widest">E-mail</p>

                <a
                  href="mailto:contact@example.com"
                  className="mt-2 block text-xs text-[#718087]"
                >
                  contact@example.com
                </a>
              </div>
            </div>

            <div className="mb-7 flex gap-4">
              <Phone size={17} strokeWidth={1.3} />

              <div>
                <p className="text-[9px] uppercase tracking-widest">
                  Téléphone
                </p>

                <p className="mt-2 text-xs text-[#718087]">+213 00 00 00 00 (exemple)</p>
              </div>
            </div>

            <div className="flex gap-4">
              <MapPin size={17} strokeWidth={1.3} />

              <div>
                <p className="text-[9px] uppercase tracking-widest">Cabinet</p>

                <p className="mt-2 text-xs leading-5 text-[#718087]">
                  Adresse à confirmer (exemple)
                  <br />
                  Algérie
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;
