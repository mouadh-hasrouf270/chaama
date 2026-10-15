import { ArrowRight } from "lucide-react";

type StepNeedProps = {
  consultation: string;
  domain: string;
  onConsultationChange: (value: string) => void;
  onDomainChange: (value: string) => void;
  onNext: () => void;
  domainOptions: string[];
};

const consultationOptions = [
  "Première consultation",
  "Avis juridique",
  "Accompagnement d’une procédure",
];


type ChoiceListProps = {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
};

function ChoiceList({ label, options, value, onChange }: ChoiceListProps) {
  return (
    <fieldset className="mb-7 border-0 p-0">
      <legend className="mb-2.5 block text-[11px] font-semibold text-[#28464d]">
        {label}
      </legend>

      <div className="grid gap-2">
        {options.map((option) => {
          const selected = value === option;

          return (
            <label
              key={option}
              className={[
                "flex min-h-10 cursor-pointer items-center gap-2.5 border px-3",
                "text-[11px] transition-all duration-200",
                selected
                  ? "border-[#9caeaa] bg-[#f0f3ef] text-[#25444b]"
                  : "border-[#e0e2dd] text-[#708589]",
                "hover:border-[#9caeaa] hover:bg-[#f0f3ef]",
              ].join(" ")}
            >
              <input
                type="radio"
                name={label}
                value={option}
                checked={selected}
                onChange={() => onChange(option)}
                className="sr-only"
              />

              <span
                className={[
                  "relative h-[9px] w-[9px] shrink-0 rounded-full border",
                  selected ? "border-[#bd914c]" : "border-[#aab5b2]",
                ].join(" ")}
              >
                {selected && (
                  <span className="absolute inset-[1px] rounded-full bg-[#bd914c]" />
                )}
              </span>

              <span>{option}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function StepNeed({
  consultation,
  domain,
  onConsultationChange,
  onDomainChange,
  onNext,
  domainOptions,
}: StepNeedProps) {
  const canContinue = Boolean(consultation && domain);

  return (
    <div className="animate-[fadeIn_0.35s_ease]">
      <ChoiceList
        label="Type de consultation"
        options={consultationOptions}
        value={consultation}
        onChange={onConsultationChange}
      />

      <ChoiceList
        label="Domaine concerné"
        options={domainOptions}
        value={domain}
        onChange={onDomainChange}
      />

      <div className="mt-8 flex justify-end border-t border-[#e0e2dd] pt-[18px]">
        <button
          type="button"
          onClick={onNext}
          disabled={!canContinue}
          className="inline-flex items-center gap-2 bg-[#8e9da0] px-[15px] py-3 text-[11px] font-semibold text-white transition-all duration-200 hover:bg-[#1b3a42] hover:-translate-y-px disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:bg-[#8e9da0]"
        >
          Continuer
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
}
