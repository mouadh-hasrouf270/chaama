import { Check } from "lucide-react";

type Step = {
  number: string;
  label: string;
};

type BookingStepperProps = {
  currentStep: number;
  onStepChange: (step: number) => void;
};

const steps: Step[] = [
  { number: "01", label: "Votre besoin" },
  { number: "02", label: "Le rendez-vous" },
  { number: "03", label: "Vos coordonnées" },
];

export default function BookingStepper({
  currentStep,
  onStepChange,
}: BookingStepperProps) {
  return (
    <nav
      className="mb-8 grid grid-cols-3 border-y border-[#dfe2dc]"
      aria-label="Étapes de prise de rendez-vous"
    >
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isActive = stepNumber === currentStep;
        const isComplete = stepNumber < currentStep;
        const isDisabled = stepNumber > currentStep;

        return (
          <button
            key={step.number}
            type="button"
            onClick={() => {
              if (!isDisabled) {
                onStepChange(stepNumber);
              }
            }}
            disabled={isDisabled}
            aria-current={isActive ? "step" : undefined}
            className={[
              "min-h-16 border-r border-[#dfe2dc] px-3 py-3 text-left transition-all duration-200",
              "last:border-r-0",
              isActive
                ? "bg-[#e7eeea] text-[#1d3d45]"
                : "bg-transparent text-[#73878a]",
              !isDisabled && !isActive ? "hover:bg-[#edf2ed]" : "",
              isDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
            ].join(" ")}
          >
            <span
              className={[
                "mb-2 block text-[8px]",
                isComplete ? "text-[#bd914c]" : "text-[#91a2a0]",
              ].join(" ")}
            >
              {isComplete ? <Check size={12} strokeWidth={2.5} /> : step.number}
            </span>

            <span className="text-[11px] font-semibold">{step.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
