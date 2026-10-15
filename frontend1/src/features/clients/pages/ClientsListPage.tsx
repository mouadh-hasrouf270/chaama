import { useState } from "react";
import useApi from "../../../hooks/useApi";
import { Link, useNavigate } from "react-router-dom";
import { Search, Plus, Mail, BriefcaseBusiness } from "lucide-react";

import { PageHeader, Card, Badge } from "../../../components/ui/InternalUI";
import ClientFormModal from "../components/ClientFormModal";


export default function ClientsListPage() {
  const [recherche, setRecherche] = useState("");

  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const navigate = useNavigate();
  const { data, loading, error, reload } = useApi(`/v1/clients/?search=${encodeURIComponent(recherche)}&page=${page}`);
  const clients = (data?.results || []).map((client: any) => ({
    id: client.id, nom: `${client.first_name} ${client.last_name}`,
    contact: client.phone, email: client.email, dossiers: "—",
  }));
  const filtres = clients;

  return (
    <div className="w-full">
      {/* =================================================
          HEADER
      ================================================= */}
      <PageHeader
        eyebrow="Clients"
        title={`${data?.count ?? "—"} clients`}
        action={
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="flex shrink-0 items-center gap-2 border border-chaama-dark bg-chaama-dark px-3 py-2.5 text-[12px] font-semibold text-white transition hover:bg-chaama-dark2 sm:px-4 sm:text-[13px]"
          >
            <Plus size={15} strokeWidth={1.8} />
            <span className="hidden xs:inline sm:inline">Nouveau client</span>
            <span className="sm:hidden">Nouveau</span>
          </button>
        }
      />

      <ClientFormModal
        open={showForm}
        onClose={() => setShowForm(false)}
        onCreated={(client) => {
          setShowForm(false);
          setRecherche("");
          setPage(1);
          reload();
          navigate(`/app/clients/${client.id}`);
        }}
      />

      {/* =================================================
          RECHERCHE
      ================================================= */}
      <div className="relative mb-5 w-full max-w-md">
        <Search
          size={15}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-chaama-muted"
        />

        <input
          value={recherche}
          onChange={(e) => { setRecherche(e.target.value); setPage(1); }}
          placeholder="Rechercher un client..."
          className="h-10 w-full border border-chaama-border bg-white pl-9 pr-3 text-[13px] text-chaama-text outline-none transition-colors placeholder:text-chaama-muted focus:border-chaama-gold"
        />
      </div>

      {loading && <p role="status">Chargement…</p>}
      {error && <p role="alert">{error}</p>}
      {(data?.next || data?.previous) && <div>
        <button disabled={!data?.previous} onClick={() => setPage(p => p - 1)}>Précédent</button>
        <span> {page} </span>
        <button disabled={!data?.next} onClick={() => setPage(p => p + 1)}>Suivant</button>
      </div>}
      {/* =================================================
          VERSION DESKTOP / TABLET
      ================================================= */}
      <Card className="hidden overflow-hidden p-0 md:block">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-chaama-border text-[11px] uppercase tracking-[0.12em] text-chaama-muted">
                <th className="px-5 py-3 font-medium">Client</th>

                <th className="px-5 py-3 font-medium">Contact</th>

                <th className="px-5 py-3 font-medium">Email</th>

                <th className="px-5 py-3 font-medium">Dossiers</th>
              </tr>
            </thead>

            <tbody>
              {filtres.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-chaama-border last:border-0 hover:bg-chaama-cream/60"
                >
                  {/* Client */}
                  <td className="px-5 py-4">
                    <Link
                      to={`/app/clients/${c.id}`}
                      className="font-medium text-chaama-text transition-colors hover:text-chaama-dark2"
                    >
                      {c.nom}
                    </Link>
                  </td>

                  {/* Contact */}
                  <td className="px-5 py-4 text-chaama-muted">{c.contact}</td>

                  {/* Email */}
                  <td className="px-5 py-4 text-chaama-muted">{c.email}</td>

                  {/* Dossiers */}
                  <td className="px-5 py-4">
                    <Badge tone="gold">{c.dossiers}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* =================================================
          VERSION MOBILE
      ================================================= */}
      <div className="space-y-3 md:hidden">
        {filtres.map((c) => (
          <Card
            key={c.id}
            className="p-4 transition-colors hover:border-chaama-gold/40"
          >
            {/* Nom + badge */}
            <div className="flex items-start justify-between gap-3">
              <Link to={`/app/clients/${c.id}`} className="min-w-0 flex-1">
                <p className="truncate text-[14px] font-semibold text-chaama-text">
                  {c.nom}
                </p>

                <p className="mt-1 text-[11px] text-chaama-muted">{c.contact}</p>
              </Link>

              <div className="shrink-0">
                <Badge tone="gold">{c.dossiers}</Badge>
              </div>
            </div>

            {/* Informations */}
            <div className="mt-4 space-y-2 border-t border-chaama-border pt-3">
              <div className="flex min-w-0 items-center gap-2">
                <Mail
                  size={13}
                  className="shrink-0 text-chaama-gold"
                  strokeWidth={1.8}
                />

                <a
                  href={`mailto:${c.email}`}
                  className="truncate text-[12px] text-chaama-muted hover:text-chaama-dark2"
                >
                  {c.email}
                </a>
              </div>

              <div className="flex items-center gap-2">
                <BriefcaseBusiness
                  size={13}
                  className="shrink-0 text-chaama-gold"
                  strokeWidth={1.8}
                />

                <span className="text-[12px] text-chaama-muted">
                  {c.dossiers} dossier
                  
                </span>
              </div>
            </div>
          </Card>
        ))}

        {/* Aucun résultat */}
        {!loading && !error && filtres.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-[13px] font-medium text-chaama-text">
              Aucun client trouvé
            </p>

            <p className="mt-1 text-[11px] text-chaama-muted">
              Essayez avec un autre nom ou une autre adresse email.
            </p>
          </Card>
        )}
      </div>

      {/* Aucun résultat desktop */}
      {!loading && !error && filtres.length === 0 && (
        <div className="hidden md:block">
          <Card className="mt-3 p-8 text-center">
            <p className="text-[13px] font-medium text-chaama-text">
              Aucun client trouvé
            </p>

            <p className="mt-1 text-[11px] text-chaama-muted">
              Essayez avec un autre nom ou une autre adresse email.
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}
