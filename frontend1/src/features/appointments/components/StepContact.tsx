import { ArrowLeft, Send } from "lucide-react";
import InputField from "../../../components/forms/InputField";
import PhoneField from "../../../components/forms/PhoneField";
import TextareaField from "../../../components/forms/TextareaField";
import CheckboxField from "../../../components/forms/CheckboxField";

type StepContactProps = {
  name: string;
  email: string;
  phone: string;
  subject: string;
  details: string;
  opposingParty: string;
  consent: boolean;
  onChange: (field: string, value: string | boolean) => void;
  onBack: () => void;
  onSubmit: () => void;
  busy?: boolean;
};

export default function StepContact({
  name,
  email,
  phone,
  subject,
  details,
  opposingParty,
  consent,
  onChange,
  onBack,
  onSubmit,
  busy = false,
}: StepContactProps) {
  const canSubmit = Boolean(
    name.trim() && email.trim() && phone.trim() && subject.trim() && details.trim().length >= 10 && consent,
  );

  return (
    <div className="transition-all duration-300">
      {/* FORM GRID */}
      <div className="mb-[26px] grid grid-cols-1 gap-0 md:grid-cols-2 md:gap-x-[26px]">
        <div className="mb-[22px]">
          <InputField
            label="Nom complet"
            value={name}
            placeholder="Votre nom"
            onChange={(value) => onChange("name", value)}
          />
        </div>

        <div className="mb-[22px]">
          <InputField
            label="Adresse e-mail"
            type="email"
            value={email}
            placeholder="vous@exemple.com"
            onChange={(value) => onChange("email", value)}
          />
        </div>

        <div className="mb-[22px]">
          <PhoneField
            label="Téléphone"
            value={phone}
            placeholder="+213 ..."
            onChange={(value) => onChange("phone", value)}
          />
        </div>

        <div className="mb-[22px]">
          <InputField
            label="Objet de la demande"
            value={subject}
            placeholder="En quelques mots"
            onChange={(value) => onChange("subject", value)}
          />
        </div>
      </div>

      {/* DETAILS */}
      <div className="mb-[22px]">
        <TextareaField
          label="Décrivez brièvement votre situation"
          value={details}
          placeholder="Les éléments essentiels de votre demande"
          rows={4}
          onChange={(value) => onChange("details", value)}
        />
      </div>

      {/* OPPOSING PARTY */}
      <div className="mb-[22px]">
        <InputField
          label="Partie adverse, si connue"
          value={opposingParty}
          placeholder="Nom ou entreprise"
          onChange={(value) => onChange("opposingParty", value)}
        />
      </div>

      {/* CONSENT */}
      <CheckboxField
        id="booking-consent"
        checked={consent}
        onChange={(checked) => onChange("consent", checked)}
        label="J’accepte que CHAAMA utilise ces informations pour traiter ma demande de rendez-vous."
      />

      {!canSubmit && <div role="status" className="mb-3 text-sm text-amber-800">
        {!name.trim() || !email.trim() || !phone.trim() || !subject.trim() ? "Complétez votre nom, e-mail, téléphone et objet. " : ""}
        {details.trim().length < 10 ? "Décrivez votre situation en au moins 10 caractères. " : ""}
        {!consent ? "Cochez la case d’acceptation des informations. " : ""}
      </div>}
      {/* ACTIONS */}
      <div className="mt-[30px] flex items-center justify-between border-t border-[#e0e2dd] pt-[18px]">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 bg-transparent px-0 py-2 text-[11px] font-semibold text-[#73878a] transition-colors hover:text-[#1b3a42]"
        >
          <ArrowLeft size={14} />
          Retour
        </button>

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || busy}
          className="inline-flex items-center gap-2 bg-[#8e9da0] px-[15px] py-3 text-[11px] font-semibold text-white transition-all duration-200 hover:-translate-y-px hover:bg-[#1b3a42] disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:bg-[#8e9da0]"
        >
          {busy ? "Envoi…" : "Envoyer la demande"}
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
