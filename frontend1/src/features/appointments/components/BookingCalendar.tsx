import { useState } from "react";

type Props = {
  value: string; min: string; max: string; weekdays: number[];
  onChange: (date: string) => void;
};

export default function BookingCalendar({ value, min, max, weekdays, onChange }: Props) {
  const [month, setMonth] = useState((value || min).slice(0, 7));
  const first = new Date(`${month}-01T12:00:00Z`);
  const offset = (first.getUTCDay() + 6) % 7;
  const count = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
  function move(delta: number) {
    const target = new Date(first);
    target.setUTCMonth(target.getUTCMonth() + delta);
    setMonth(target.toISOString().slice(0, 7));
  }
  return <section aria-label="Calendrier de réservation" className="border border-[#d7dcd6] p-4">
    <div className="mb-4 flex items-center justify-between">
      <button type="button" aria-label="Mois précédent" disabled={month <= min.slice(0, 7)} onClick={() => move(-1)} className="p-2 disabled:opacity-30">←</button>
      <h3 aria-live="polite" className="font-semibold">{first.toLocaleDateString("fr", { timeZone: "UTC", month: "long", year: "numeric" })}</h3>
      <button type="button" aria-label="Mois suivant" disabled={month >= max.slice(0, 7)} onClick={() => move(1)} className="p-2 disabled:opacity-30">→</button>
    </div>
    <div className="grid grid-cols-7 gap-1 text-center text-sm">
      {["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map(day => <span key={day} className="py-2 text-xs text-[#73878a]">{day}</span>)}
      {Array.from({ length: offset }, (_, i) => <span key={`blank-${i}`} />)}
      {Array.from({ length: count }, (_, i) => {
        const date = `${month}-${String(i + 1).padStart(2, "0")}`;
        const weekday = (new Date(`${date}T12:00:00Z`).getUTCDay() + 6) % 7;
        return <button type="button" key={date} aria-label={date} aria-pressed={value === date}
          disabled={date < min || date > max || !weekdays.includes(weekday)} onClick={() => onChange(date)}
          className={`min-h-10 rounded border border-transparent focus-visible:outline-2 focus-visible:outline-[#bd914c] disabled:opacity-25 ${value === date ? "bg-[#1b3a42] text-white" : "enabled:hover:border-[#bd914c]"}`}>{i + 1}</button>;
      })}
    </div>
  </section>;
}
