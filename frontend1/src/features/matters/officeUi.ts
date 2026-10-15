export const control = "w-full rounded border border-ch2ma-border bg-white px-3 py-2 text-sm outline-none focus:border-ch2ma-gold";
export const button = "rounded border border-ch2ma-dark bg-ch2ma-dark px-4 py-2 text-sm text-white disabled:opacity-40";
export const statuses: Record<string, string> = { OPEN: "Ouvert", ACTIVE: "En traitement", WAITING: "En attente", CLOSED: "Clôturé", ARCHIVED: "Archivé" };
export const transitions: Record<string, string[]> = { OPEN: ["ACTIVE", "WAITING", "CLOSED"], ACTIVE: ["WAITING", "CLOSED"], WAITING: ["ACTIVE", "CLOSED"], CLOSED: ["ACTIVE", "ARCHIVED"], ARCHIVED: [] };
export const invoiceStatuses: Record<string, string> = { DRAFT: "Brouillon", ISSUED: "Émise", PARTIALLY_PAID: "Partiellement réglée", PAID: "Réglée", CANCELLED: "Annulée" };
export const money = (value: string | number) => Number(value).toLocaleString("fr-DZ", { style: "currency", currency: "DZD" });
