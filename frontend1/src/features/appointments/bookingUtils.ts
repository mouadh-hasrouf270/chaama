export const officeTimezone = "Africa/Algiers";
export const statusLabels: Record<string, string> = {
  PENDING: "À confirmer", CONFIRMED: "Confirmé", CANCELLED: "Annulé", COMPLETED: "Terminé",
};
export const modeLabels: Record<string, string> = {
  OFFICE: "Au cabinet", VIDEO: "Visioconférence", PHONE: "Téléphone",
};
export function officeDate(value: string | Date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: officeTimezone, year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date(value));
  const get = (type: string) => parts.find(p => p.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}
export function officeTime(value: string) {
  return new Date(value).toLocaleTimeString("fr", { timeZone: officeTimezone, hour: "2-digit", minute: "2-digit" });
}
export function officeDateTime(value: string) {
  return new Date(value).toLocaleString("fr", { timeZone: officeTimezone, dateStyle: "medium", timeStyle: "short" });
}
export function shiftDate(value: string, days: number) {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
