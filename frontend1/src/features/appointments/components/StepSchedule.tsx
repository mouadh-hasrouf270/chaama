import { ArrowLeft, ArrowRight, Clock3 } from "lucide-react";
import DateField from "../../../components/forms/DateField";
import SelectField from "../../../components/forms/SelectField";

type StepScheduleProps = {
  date: string;
  time: string;
  mode: string;
  onDateChange: (value: string) => void;
  onTimeChange: (value: string) => void;
  onModeChange: (value: string) => void;
  onBack: () => void;
  onNext: () => void;
  availableTimes: { value: string; label: string }[];
  noSlots: boolean;
};

const modes = [
  {
    value: "cabinet",
    label: "Au cabinet, Alger Centre",
  },
  {
    value: "visio",
    label: "Visioconférence sécurisée",
  },
  {
    value: "telephone",
    label: "Par téléphone",
  },
];

export default function StepSchedule({
  date,
  time,
  mode,
  onDateChange,
  onTimeChange,
  onModeChange,
  onBack,
  onNext,
  availableTimes,
  noSlots,
}: StepScheduleProps) {
  // Use local calendar components, never a locale-dependent string such as DD/MM/YYYY.
  const algerDate = new Date(new Date().toLocaleString("en-US", { timeZone: "Africa/Algiers" }));
  const isoDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const today = isoDay(algerDate);
  const lastDate = new Date(algerDate);
  lastDate.setDate(lastDate.getDate() + 90);
  const maxDate = isoDay(lastDate);
  const validDate = Boolean(date && date >= today && date <= maxDate);
  const suggestedTimes = Array.from({ length: 19 }, (_, i) => {
    const total = 9 * 60 + i * 30;
    const value = `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
    return { value, label: value };
  });

  const validTime = noSlots ? /^([01]\d|2[0-3]):[0-5]\d$/.test(time) : availableTimes.some(slot => slot.value === time);
  const canContinue = Boolean(validDate && time && mode && validTime);

  return (
    <div className="transition-all duration-300">
      {/* DATE + TIME */}
      <div className="mb-[26px] grid grid-cols-1 gap-0 md:grid-cols-2 md:gap-x-[26px]">
        <div className="mb-[22px]">
          <DateField
            label="Date souhaitée"
            value={date}
            min={today}
            max={maxDate}
            onChange={onDateChange}
            required
          />
        </div>

        <label className="mb-[22px] block">
          <span className="mb-2.5 block text-[11px] font-semibold text-[#28464d]">
            Heure souhaitée
          </span>

          {noSlots ? <div>
            <select
              aria-label="Heure souhaitée"
              value={suggestedTimes.some(option => option.value === time) ? time : ""}
              onChange={event => onTimeChange(event.target.value)}
              disabled={!validDate}
              className="w-full border border-[#d7dcd6] bg-white px-4 py-3 text-sm text-[#1b3a42] outline-none focus:border-[#a47a39] disabled:opacity-50"
            >
              <option value="">Choisissez votre heure préférée</option>
              {suggestedTimes.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <p className="mt-2 text-xs text-[#667b7d]">Cette heure est une préférence, pas une réservation confirmée. Le cabinet vous contactera.</p>
          </div> : <div className="relative flex items-center">
            <select
              value={time}
              onChange={(event) => onTimeChange(event.target.value)}
              disabled={!validDate || availableTimes.length === 0}
              className="w-full border-0 border-b border-[#d7dcd6] bg-transparent px-0 py-2 pb-[11px] text-xs text-[#1b3a42] outline-none focus:border-[#a47a39] disabled:opacity-50"
            >
              <option value="">Sélectionnez un créneau</option>
              {availableTimes.map(slot => <option key={slot.value} value={slot.value}>{slot.label}</option>)}
            </select>
            <Clock3 size={15} className="pointer-events-none absolute right-0 text-[#748688]" />
          </div>}
        </label>
      </div>

      {/* MODE */}
      <SelectField
        label="Mode d’échange"
        value={mode}
        onChange={onModeChange}
        options={modes}
        placeholder="Sélectionnez un mode"
        required
      />

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
          onClick={onNext}
          disabled={!canContinue}
          className="inline-flex items-center gap-2 bg-[#8e9da0] px-[15px] py-3 text-[11px] font-semibold text-white transition-all duration-200 hover:-translate-y-px hover:bg-[#1b3a42] disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:bg-[#8e9da0]"
        >
          Continuer
          <ArrowRight size={15} />
        </button>
      </div>
      {!canContinue && <p role="status" className="mt-3 text-sm text-amber-800">{!validDate ? "Choisissez une date entre aujourd’hui et les 90 prochains jours." : !time ? "Indiquez votre heure préférée." : !validTime ? "Choisissez un créneau valide." : !mode ? "Choisissez un mode d’échange." : "Complétez les informations de rendez-vous."}</p>}
    </div>
  );
}
