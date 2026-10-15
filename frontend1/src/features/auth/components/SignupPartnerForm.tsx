import { useState } from "react";
import api, { errorMessage } from "../../../api/client";
import { FileText, Info, Upload } from "lucide-react";

type Specialty = {
  id: string;
  label: string;
};

const specialties: Specialty[] = [
  {
    id: "droit-affaires",
    label: "Droit des affaires",
  },
  {
    id: "droit-travail",
    label: "Droit du travail",
  },
  {
    id: "droit-fiscal",
    label: "Droit fiscal",
  },
  {
    id: "droit-immobilier",
    label: "Droit immobilier",
  },
  {
    id: "droit-penal",
    label: "Droit pénal",
  },
  {
    id: "droit-famille",
    label: "Droit de la famille",
  },
  {
    id: "droit-public",
    label: "Droit public",
  },
  {
    id: "propriete-intellectuelle",
    label: "Propriété intellectuelle",
  },
];

type FieldRowProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
};

function FieldRow({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: FieldRowProps) {
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

type SignupPartnerFormProps = {
  onSubmitted: () => void;
};

export default function SignupPartnerForm({
  onSubmitted,
}: SignupPartnerFormProps) {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [cabinet, setCabinet] = useState("");
  const [email, setEmail] = useState("");
  const [barNumber, setBarNumber] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);

  const toggleSpecialty = (id: string) => {
    setSelectedSpecialties((previous) =>
      previous.includes(id)
        ? previous.filter((specialty) => specialty !== id)
        : [...previous, id],
    );
  };

  const canSubmit =
    fullName.trim().length > 1 &&
    cabinet.trim().length > 1 &&
    email.includes("@") && phone.trim().length >= 7 &&
    barNumber.trim().length > 2 &&
    jurisdiction.trim().length > 1 &&
    selectedSpecialties.length > 0 &&
    fileName !== null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!canSubmit) return;

    setSending(true); setError("");
    const payload = new FormData();
    Object.entries({ full_name: fullName, cabinet, email, phone, bar_number: barNumber, jurisdiction, specialties: JSON.stringify(selectedSpecialties) }).forEach(([key, value]) => payload.append(key, value));
    if (file) payload.append("proof", file);
    try { await api.post("/accounts/partner-applications/apply/", payload); onSubmitted(); }
    catch (err) { setError(errorMessage(err)); }
    finally { setSending(false); }
  };

  return (
    <>
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-chaama-gold">
        Avocat externe
      </p>

      <h2 className="font-display text-[38px] leading-tight tracking-[-1.2px] text-chaama-text sm:text-[44px]">
        Demander à devenir partenaire
      </h2>

      <p className="mt-3 text-[16px] leading-7 text-chaama-muted">
        Renseignez vos informations professionnelles. Votre compte restera en
        attente jusqu'à validation de votre justificatif.
      </p>

      <div className="mb-6 mt-6 flex items-start gap-3 border border-chaama-gold/30 bg-chaama-green px-4 py-3.5">
        <Info
          size={16}
          strokeWidth={1.6}
          className="mt-0.5 shrink-0 text-chaama-gold"
        />

        <p className="text-[12px] leading-5 text-chaama-muted">
          Chama validera manuellement votre justificatif de barreau. Vous
          recevrez ensuite un lien d'activation par email.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FieldRow
          label="Nom et prénom"
          value={fullName}
          onChange={setFullName}
          placeholder="Ex. Marie Dupont"
        />

        <FieldRow
          label="Cabinet / Structure"
          value={cabinet}
          onChange={setCabinet}
          placeholder="Ex. Cabinet Dupont & Associés"
        />

        <FieldRow label="Téléphone / WhatsApp" value={phone} onChange={setPhone} placeholder="+213 ..." />

        <FieldRow
          label="Email professionnel"
          value={email}
          onChange={setEmail}
          placeholder="vous@cabinet.fr"
          type="email"
        />

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FieldRow
            label="N° de barreau"
            value={barNumber}
            onChange={setBarNumber}
            placeholder="Ex. 123456"
          />

          <FieldRow
            label="Juridiction / Barreau"
            value={jurisdiction}
            onChange={setJurisdiction}
            placeholder="Ex. Barreau de Paris"
          />
        </div>

        <div>
          <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
            Spécialité(s)
          </span>

          <div className="flex flex-wrap gap-2">
            {specialties.map((specialty) => {
              const selected = selectedSpecialties.includes(specialty.id);

              return (
                <button
                  key={specialty.id}
                  type="button"
                  onClick={() => toggleSpecialty(specialty.id)}
                  className={[
                    "cursor-pointer border px-3.5 py-2 text-[12px] font-medium transition-all duration-200",
                    selected
                      ? "border-chaama-dark bg-chaama-dark text-chaama-cream"
                      : "border-chaama-border bg-transparent text-chaama-muted hover:border-chaama-gold hover:text-chaama-text",
                  ].join(" ")}
                >
                  {specialty.label}
                </button>
              );
            })}
          </div>

          {selectedSpecialties.length > 0 && (
            <p className="mt-2 text-[11px] text-chaama-muted">
              {selectedSpecialties.length} spécialité
              {selectedSpecialties.length > 1 ? "s" : ""} sélectionnée
              {selectedSpecialties.length > 1 ? "s" : ""}
            </p>
          )}
        </div>

        <div>
          <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
            Justificatif de barreau
          </span>

          <label
            className={[
              "flex h-[72px] w-full cursor-pointer items-center gap-4 border px-5 transition-all duration-200",
              fileName
                ? "border-chaama-dark bg-chaama-green"
                : "border-chaama-border bg-chaama-cream hover:border-chaama-gold hover:bg-chaama-green/40",
            ].join(" ")}
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center bg-chaama-dark text-chaama-cream">
              <Upload size={17} strokeWidth={1.6} />
            </div>

            <div className="min-w-0">
              <p className="truncate text-[13px] font-semibold text-chaama-text">
                {fileName ?? "Téléverser un document"}
              </p>

              <p className="mt-0.5 text-[11px] text-chaama-muted">
                PDF, JPG ou PNG — carte de barreau ou attestation
              </p>
            </div>

            {fileName && (
              <FileText
                size={18}
                strokeWidth={1.5}
                className="ml-auto shrink-0 text-chaama-gold"
              />
            )}

            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];

                if (file) {
                  setFileName(file.name);
                  setFile(file);
                }
              }}
            />
          </label>
        </div>

        {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={!canSubmit || sending}
          className="mt-7 h-[54px] w-full cursor-pointer bg-chaama-dark text-[14px] font-semibold text-white transition hover:bg-chaama-dark2 disabled:cursor-not-allowed disabled:bg-chaama-border disabled:text-chaama-muted"
        >
          {sending ? "Envoi en cours…" : "Soumettre ma candidature"}
        </button>
      </form>

      <p className="mt-5 text-center text-[11px] leading-5 text-chaama-muted">
        En soumettant, vous acceptez que vos informations soient examinées par
        le cabinet dans le cadre du processus de vérification.
      </p>
    </>
  );
}
