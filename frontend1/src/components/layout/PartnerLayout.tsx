import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  Milestone,
  FileSignature,
  Wallet,
  UserRound,
  MessageSquarePlus,
  LogOut,
} from "lucide-react";

const navItems = [
  {
    to: "/portail",
    label: "Tableau de bord",
    icon: LayoutDashboard,
    end: true,
  },
  { to: "/portail/opportunites", label: "Opportunités", icon: Briefcase },
  { to: "/portail/jalons", label: "Jalons", icon: Milestone },
  { to: "/portail/plaidoiries", label: "Plaidoiries", icon: FileSignature },
  { to: "/portail/retrocession", label: "Rétrocession", icon: Wallet },
  { to: "/portail/profil", label: "Mon profil", icon: UserRound },
  {
    to: "/portail/demande-assistance",
    label: "Demande d'assistance",
    icon: MessageSquarePlus,
  },
];

export default function PartnerLayout() {
  return (
    <div className="flex min-h-screen bg-chaama-cream">
      <aside className="flex w-64 shrink-0 flex-col justify-between bg-chaama-dark px-6 py-8 text-chaama-cream">
        <div>
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center border border-chaama-gold font-display text-xl text-chaama-gold">
              C
            </div>
            <span className="text-[11px] font-medium uppercase tracking-[0.34em] text-chaama-cream/80">
              CHAAMA
            </span>
          </div>

          <nav className="flex flex-col gap-1">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex items-center gap-3 border-l-2 px-3 py-2.5 text-[13px] transition-colors ${
                    isActive
                      ? "border-chaama-gold bg-white/5 text-chaama-gold"
                      : "border-transparent text-chaama-cream/70 hover:border-chaama-gold/40 hover:text-chaama-cream"
                  }`
                }
              >
                <Icon size={17} strokeWidth={1.7} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="border-t border-white/10 pt-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-chaama-gold/20 text-[13px] font-semibold text-chaama-gold">
              LK
            </div>
            <div>
              <p className="text-[13px] font-medium text-chaama-cream">
                Maître Lina Kaci
              </p>
              <p className="text-[11px] text-chaama-cream/50">
                Avocat partenaire
              </p>
            </div>
          </div>
          <button
            type="button"
            className="flex items-center gap-2 text-[12px] text-chaama-cream/60 transition hover:text-chaama-gold"
          >
            <LogOut size={14} strokeWidth={1.8} /> Déconnexion
          </button>
        </div>
      </aside>

      <main className="flex-1 px-10 py-10">
        <Outlet />
      </main>
    </div>
  );
}
