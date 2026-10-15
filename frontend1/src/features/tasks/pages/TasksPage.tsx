import { useState } from "react";
import { PageHeader, Card, Badge } from "../../../components/ui/InternalUI";

type Statut = "À faire" | "En cours" | "Terminée" | "En retard";

const taches: Array<{
  titre: string;
  dossier: string;
  echeance: string;
  statut: Statut;
}> = [
  {
    titre: "Déposer les conclusions",
    dossier: "Atlas Import c/ Numidia",
    echeance: "Aujourd'hui",
    statut: "En retard",
  },
  {
    titre: "Préparer le dossier de plaidoirie",
    dossier: "Benziane c/ CNAS",
    echeance: "Demain",
    statut: "En cours",
  },
  {
    titre: "Relire le projet de convention",
    dossier: "Succession Meziane",
    echeance: "Cette semaine",
    statut: "À faire",
  },
  {
    titre: "Envoyer les pièces au client",
    dossier: "SCI Hamdi",
    echeance: "Fait le 12 sept.",
    statut: "Terminée",
  },
];

const statutTone: Record<Statut, "alert" | "gold" | "muted" | "green"> = {
  "En retard": "alert",
  "En cours": "gold",
  "À faire": "muted",
  Terminée: "green",
};
const filtres: Array<Statut | "Toutes"> = [
  "Toutes",
  "À faire",
  "En cours",
  "En retard",
  "Terminée",
];

export default function TasksPage() {
  const [filtre, setFiltre] = useState<Statut | "Toutes">("Toutes");
  const resultats = taches.filter(
    (t) => filtre === "Toutes" || t.statut === filtre,
  );

  return (
    <div>
      <PageHeader
        eyebrow="Tâches"
        title="Toutes mes tâches"
        subtitle="Tous dossiers confondus."
      />

      <div className="mb-5 flex flex-wrap gap-2">
        {filtres.map((f) => (
          <button
            key={f}
            onClick={() => setFiltre(f)}
            className={`border px-3.5 py-1.5 text-[12px] font-medium transition ${
              filtre === f
                ? "border-chaama-dark bg-chaama-dark text-white"
                : "border-chaama-border text-chaama-muted hover:border-chaama-dark hover:text-chaama-dark"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <Card>
        {resultats.map((t) => (
          <div
            key={t.titre}
            className="flex items-center justify-between border-b border-chaama-border p-4 last:border-0"
          >
            <div>
              <p className="text-[13px] font-medium text-chaama-text">
                {t.titre}
              </p>
              <p className="mt-0.5 text-[12px] text-chaama-muted">
                {t.dossier} · {t.echeance}
              </p>
            </div>
            <Badge tone={statutTone[t.statut]}>{t.statut}</Badge>
          </div>
        ))}
      </Card>
    </div>
  );
}
