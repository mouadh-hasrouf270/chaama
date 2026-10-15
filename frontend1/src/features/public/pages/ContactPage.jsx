import { useState } from "react";
import InputField from "../../../components/forms/InputField";
import PhoneField from "../../../components/forms/PhoneField";
import TextareaField from "../../../components/forms/TextareaField";

const ContactPage = () => {
 const [notice,setNotice]=useState(false);
  return (
    <main className="bg-[#f8f6ef] text-[#193a42]">
      {/* =====================================================
          HEADER / INTRO
      ===================================================== */}
      <section className="border-b border-[#193a42]/10">
        <div className="mx-auto w-full max-w-[1300px] px-5 py-15 md:px-8 lg:py-15">
          {/* Label */}
          <div className="mb-7 flex items-center gap-3">
            <span className="h-px w-10 bg-[#193a42]" />

            <span
              className="
                font-mono
                text-[9px]
                font-bold
                uppercase
                tracking-[0.28em]
                text-[#193a42]
              "
            >
              Contact
            </span>
          </div>

          {/* Title */}
          <h1
            className="
              max-w-[900px]
              font-display
              text-5xl
              leading-[0.95]
              tracking-[-1.5px]
              text-[#193a42]
              sm:text-6xl
              lg:text-[76px]
            "
          >
            Parlons de ce qui vous
            <br />
            <span className="italic">amène ici.</span>
          </h1>

          {/* Description */}
          <p
            className="
              mt-8
              max-w-[620px]
              text-base
              leading-8
              text-[#718087]
              sm:text-[17px]
            "
          >
            Un premier message suffit. Nous vous répondrons avec discrétion et
            vous indiquerons la meilleure manière d’avancer.
          </p>
        </div>
      </section>

      {/* =====================================================
          CONTACT CONTENT
      ===================================================== */}
      <section>
        <div
          className="
            mx-auto
            flex
            w-full
            max-w-[1300px]
            flex-col
            gap-16
            px-5
            py-15
            md:px-8
            lg:flex-row
            lg:gap-24
            lg:py-15
          "
        >
          {/* =================================================
              FORMULAIRE
          ================================================= */}
          <div className="w-full lg:max-w-[700px]">
            <div className="mb-10">
              <h2 className="font-display text-3xl text-[#193a42]">
                Votre demande
              </h2>

              <p className="mt-3 text-sm leading-6 text-[#718087]">
                Décrivez-nous votre situation afin que nous puissions comprendre
                votre besoin.
              </p>
            </div>

            <form className="space-y-8" onSubmit={(e)=>{ e.preventDefault(); setNotice(true); }}>
              {/* Nom + Email */}
              <div className="grid gap-8 sm:grid-cols-2">
                <InputField label="Nom complet" id="name" required />

                <InputField
                  label="Adresse e-mail"
                  id="email"
                  type="email"
                  required
                />
              </div>

              {/* Téléphone + Objet */}
              <div className="grid gap-8 sm:grid-cols-2">
                <PhoneField label="Téléphone" id="phone" />

                <InputField label="Objet" id="subject" required />
              </div>

              {/* Message */}
              <TextareaField
                label="Votre message"
                id="message"
                rows={5}
                required
              />

              {/* Confidentialité */}
              <p className="max-w-[600px] text-[11px] leading-5 text-[#718087]">
                Les informations transmises sont utilisées uniquement pour
                répondre à votre demande et sont traitées avec confidentialité.
              </p>

              {notice && <p role="status" className="text-sm text-amber-900">Le formulaire de contact nécessite une adresse e-mail vérifiée ou un service de réception. Aucune demande n’a été envoyée.</p>}
              {/* Submit */}
              <button
                type="submit"
                className="
                  group
                  inline-flex
                  min-h-[48px]
                  items-center
                  gap-4
                  bg-[#193a42]
                  px-6
                  text-xs
                  font-semibold
                  text-[#f8f6ef]
                  transition-all
                  duration-300
                  hover:bg-[#244b54]
                "
              >
                Vérifier l’envoi
              </button>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
};

export default ContactPage;
