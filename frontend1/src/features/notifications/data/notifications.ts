export type Notification = {
  id: number;
  titre: string;
  date: string;
  lu: boolean;
};

export const initialNotifications: Notification[] = [
  {
    id: 1,
    titre: "Échéance demain — Benziane c/ CNAS",
    date: "il y a 1h",
    lu: false,
  },
  {
    id: 2,
    titre: "Nouveau RDV client confirmé",
    date: "il y a 3h",
    lu: false,
  },
  {
    id: 3,
    titre: "Devis DEV-2026-013 validé par Chama",
    date: "hier",
    lu: true,
  },
  {
    id: 4,
    titre: "Nouveau document ajouté au dossier",
    date: "hier",
    lu: true,
  },
  {
    id: 5,
    titre: "Paiement reçu — Dossier Benali",
    date: "il y a 2 jours",
    lu: true,
  },
  {
    id: 6,
    titre: "Nouvelle tâche assignée",
    date: "il y a 2 jours",
    lu: true,
  },
];
