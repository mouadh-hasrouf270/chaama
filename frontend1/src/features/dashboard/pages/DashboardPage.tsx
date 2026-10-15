import useApi from "../../../hooks/useApi";
import {
  Gavel,
  ListChecks,
  FolderOpen,
  Users,
  Clock3,
  MapPin,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

import { Link } from "react-router-dom";

import {
  PageHeader,
  StatCard,
  Card,
  Badge,
} from "../../../components/ui/InternalUI";

export default function DashboardPage() {
  const { data, loading, error } = useApi("/v1/dashboard/");
  const { data: user } = useApi("/accounts/me/");
  const audiencesDuJour = (data?.today_appointments || []).map((a: any) => ({
    id: a.id, heure: new Date(a.start_at).toLocaleTimeString("fr", { hour: "2-digit", minute: "2-digit" }),
    dossier: a.client_name || "Consultation", tribunal: a.consultation_type,
  }));
  const tachesPrioritaires = (data?.upcoming_appointments || []).map((a: any) => ({
    id: a.id, titre: a.client_name || "Consultation",
    echeance: new Date(a.start_at).toLocaleString("fr"), priorite: "normale", statut: a.status,
  }));
  return (
    <div className="w-full">
      {/* =====================================================
          HEADER
      ===================================================== */}
      <PageHeader
        eyebrow="Tableau de bord"
        title={`Bonjour, ${user?.first_name || user?.username || ""}`}
        subtitle={new Date().toLocaleDateString("fr", { weekday: "long", day: "numeric", month: "long" })}
      />

      {(user?.role === "SUPER_ADMIN" || user?.is_superuser) && <Link to="/app/partner-applications" className="mb-6 block border-l-4 border-chaama-gold bg-white p-5 font-semibold hover:bg-chaama-green">Demandes de partenariat → Examiner et accepter les candidatures</Link>}
      {loading && <p role="status">Chargement…</p>}
      {error && <p role="alert">{error}</p>}
      {/* =====================================================
          STATISTIQUES
      ===================================================== */}
      <div className="mb-6 grid grid-cols-2 items-stretch gap-3 sm:mb-8 sm:gap-4 lg:grid-cols-4">
        <Link
          to="/app/clients"
          className="group block h-[140px] w-full rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-chaama-gold sm:h-[150px]"
        >
          <StatCard
            label="Clients actifs"
            value={String(data?.clients_count ?? "—")}
            icon={Users}
            className="h-[140px] sm:h-[150px]"
          />
        </Link>

        <Link
          to="/app"
          className="group block h-[140px] w-full rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-chaama-gold sm:h-[150px]"
        >
          <StatCard
            label="Notifications non lues"
            value={String(data?.unread_notifications ?? "—")}
            icon={FolderOpen}
            className="h-[140px] sm:h-[150px]"
          />
        </Link>

        <Link
          to="/app/calendar"
          className="group block h-[140px] w-full rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-chaama-gold sm:h-[150px]"
        >
          <StatCard
            label="Rendez-vous aujourd’hui"
            value={String(data?.today_appointments?.length ?? "—")}
            icon={Gavel}
            className="h-[140px] sm:h-[150px]"
          />
        </Link>

        <Link
          to="/app/calendar"
          className="group block h-[140px] w-full rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-chaama-gold sm:h-[150px]"
        >
          <StatCard
            label="Formulaires à examiner"
            value={String(data?.pending_intakes ?? "—")}
            icon={ListChecks}
            className="h-[140px] sm:h-[150px]"
          />
        </Link>
      </div>

      {/* =====================================================
          CONTENU PRINCIPAL
      ===================================================== */}
      <div className="grid grid-cols-1 items-stretch gap-4 sm:gap-6 lg:grid-cols-2">
        {/* ===================================================
            AUDIENCES DU JOUR
        =================================================== */}
        <Card className="flex h-full flex-col overflow-hidden border border-chaama-border bg-chaama-cream p-0 shadow-none">
          {/* Header */}
          <div className="flex shrink-0 items-center justify-between border-b border-chaama-border px-4 py-4 sm:px-6 sm:py-5">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-chaama-dark text-chaama-gold">
                <Gavel size={18} strokeWidth={1.8} />
              </div>

              <div className="min-w-0">
                <h2 className="truncate text-[17px] text-chaama-text sm:text-[19px]">
                  Rendez-vous du jour
                </h2>

                <p className="mt-0.5 truncate text-[11px] text-chaama-muted">
                  Vos consultations du jour
                </p>
              </div>
            </div>

            <Link
              to="/app/calendar"
              className="ml-3 flex shrink-0 items-center gap-1 text-[12px] font-semibold text-chaama-gold transition-colors hover:text-chaama-dark2"
            >
              <span className="hidden sm:inline">Voir tout</span>

              <ArrowRight size={13} />
            </Link>
          </div>

          {/* Liste */}
          <div className="flex-1 p-2 sm:p-3">
            <ul className="space-y-2">
              {!loading && !error && !audiencesDuJour.length && <li>Aucun rendez-vous aujourd’hui.</li>}
              {audiencesDuJour.map((a) => (
                <li key={a.id}>
                  <Link
                    to="/app/calendar"
                    className="group flex min-w-0 items-center gap-3 rounded-xl border border-transparent bg-white px-3 py-3 outline-none transition-all hover:border-chaama-border hover:bg-chaama-green/30 focus-visible:ring-2 focus-visible:ring-chaama-gold sm:gap-4 sm:px-4 sm:py-4"
                  >
                    {/* Heure */}
                    <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-xl border border-chaama-border bg-chaama-green sm:h-12 sm:w-12">
                      <Clock3
                        size={13}
                        className="mb-0.5 text-chaama-dark2 sm:size-[14px]"
                      />

                      <span className="text-[10px] font-bold text-chaama-dark2 sm:text-[11px]">
                        {a.heure}
                      </span>
                    </div>

                    {/* Informations */}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12px] font-semibold text-chaama-text sm:text-[13px]">
                        {a.dossier}
                      </p>

                      <div className="mt-1.5 flex min-w-0 items-center gap-1.5">
                        <MapPin
                          size={12}
                          className="shrink-0 text-chaama-muted"
                        />

                        <p className="truncate text-[11px] text-chaama-muted sm:text-[11.5px]">
                          {a.tribunal}
                        </p>
                      </div>
                    </div>

                    <ArrowRight
                      size={15}
                      className="shrink-0 text-chaama-muted transition-transform group-hover:translate-x-1 group-hover:text-chaama-gold"
                    />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Footer */}
          <div className="mt-auto shrink-0 border-t border-chaama-border px-4 py-3 sm:px-6">
            <p className="text-[11px] text-chaama-muted">
              <span className="font-semibold text-chaama-dark2">
                {audiencesDuJour.length}
              </span>{" "}
              rendez-vous prévus aujourd’hui
            </p>
          </div>
        </Card>

        {/* ===================================================
            TÂCHES PRIORITAIRES
        =================================================== */}
        <Card className="flex h-full flex-col overflow-hidden border border-chaama-border bg-chaama-cream p-0 shadow-none">
          {/* Header */}
          <div className="flex shrink-0 items-center justify-between border-b border-chaama-border px-4 py-4 sm:px-6 sm:py-5">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-chaama-dark text-chaama-gold">
                <ListChecks size={18} strokeWidth={1.8} />
              </div>

              <div className="min-w-0">
                <h2 className="truncate text-[17px] text-chaama-text sm:text-[19px]">
                  Prochains rendez-vous
                </h2>

                <p className="mt-0.5 truncate text-[11px] text-chaama-muted">
                  Vos prochaines consultations
                </p>
              </div>
            </div>

            <Link
              to="/app/calendar"
              className="ml-3 flex shrink-0 items-center gap-1 text-[12px] font-semibold text-chaama-gold transition-colors hover:text-chaama-dark2"
            >
              <span className="hidden sm:inline">Voir tout</span>

              <ArrowRight size={13} />
            </Link>
          </div>

          {/* Liste */}
          <div className="flex-1 p-2 sm:p-3">
            <ul className="space-y-2">
              {!loading && !error && !tachesPrioritaires.length && <li>Aucun rendez-vous à venir.</li>}
              {tachesPrioritaires.map((t) => (
                <li key={t.id}>
                  <Link
                    to="/app/calendar"
                    className="group flex min-w-0 items-center gap-3 rounded-xl border border-transparent bg-white px-3 py-3 outline-none transition-all hover:border-chaama-border hover:bg-chaama-green/30 focus-visible:ring-2 focus-visible:ring-chaama-gold sm:gap-4 sm:px-4 sm:py-4"
                  >
                    {/* Icône */}
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-chaama-border bg-chaama-green">
                      {t.priorite === "urgente" ? (
                        <Clock3 size={15} className="text-chaama-dark2" />
                      ) : (
                        <CheckCircle2 size={15} className="text-chaama-dark2" />
                      )}
                    </div>

                    {/* Informations */}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12px] font-semibold text-chaama-text sm:text-[13px]">
                        {t.titre}
                      </p>

                      <p className="mt-1 truncate text-[11px] text-chaama-muted sm:text-[11.5px]">
                        Échéance : {t.echeance}
                      </p>
                    </div>

                    {/* Badge */}
                    <div className="shrink-0">
                      <Badge
                        tone={t.priorite === "urgente" ? "alert" : "muted"}
                      >
                        {t.statut}
                      </Badge>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Footer */}
          <div className="mt-auto shrink-0 border-t border-chaama-border px-4 py-3 sm:px-6">
            <p className="text-[11px] text-chaama-muted">
              <span className="font-semibold text-chaama-dark2">
                {tachesPrioritaires.length}
              </span>{" "}
              rendez-vous à venir
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
