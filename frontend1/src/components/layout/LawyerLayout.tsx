import useApi from "../../hooks/useApi";
import { logout } from "../../api/auth.api";
import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  CalendarDays,
  ListChecks,
  Receipt,
  UserRoundCheck,
  LogOut,
  X,
  Menu,
} from "lucide-react";

import NotificationDropdown from "../../features/notifications/components/NotificationDropdown";

const mainNav = [
  {
    to: "/app",
    label: "Tableau de bord",
    icon: LayoutDashboard,
    end: true,
  },
  {
    to: "/app/clients",
    label: "Clients",
    icon: Users,
  },
  {
    to: "/app/matters",
    label: "Dossiers",
    icon: FolderOpen,
  },
  {
    to: "/app/calendar",
    label: "Calendrier",
    icon: CalendarDays,
  },
  {
    to: "/app/tasks",
    label: "Tâches",
    icon: ListChecks,
  },
  { to: "/app/partner-applications", label: "Demandes partenaires", icon: UserRoundCheck },
  {
    to: "/app/billing",
    label: "Facturation",
    icon: Receipt,
  },
];

export default function LawyerLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { data: user } = useApi("/accounts/me/");
  const initials = [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join("") || user?.username?.[0] || "";
  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username : "";
  const handleLogout = async () => {
    try { await logout(); } catch { /* Local session is cleared even if revocation is unavailable. */ }
  };

  /* Bloquer le scroll quand le menu mobile est ouvert */
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <div className="flex min-h-screen bg-chaama-cream">
      {/* =====================================================
          OVERLAY MOBILE
      ====================================================== */}
      {menuOpen && (
        <button
          type="button"
          aria-label="Fermer le menu"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
        />
      )}

      {/* =====================================================
          SIDEBAR
      ====================================================== */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50
          flex w-[270px] shrink-0 flex-col justify-between
          bg-chaama-dark px-5 py-6 text-chaama-cream
          transition-transform duration-300
          lg:static lg:w-64 lg:translate-x-0
          lg:px-6 lg:py-8
          ${menuOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div>
          {/* Logo */}
          <div className="mb-10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center border border-chaama-gold font-display text-xl text-chaama-gold">
                C
              </div>

              <span className="text-[11px] font-medium uppercase tracking-[0.34em] text-chaama-cream/80">
                CHAAMA
              </span>
            </div>

            <button
              type="button"
              onClick={() => setMenuOpen(false)}
              className="flex h-9 w-9 items-center justify-center text-chaama-cream/70 transition-colors hover:text-chaama-gold lg:hidden"
              aria-label="Fermer le menu"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex flex-col gap-1">
            {mainNav.filter(item => item.to !== "/app/partner-applications" || user?.role === "SUPER_ADMIN" || user?.is_superuser).map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={() => setMenuOpen(false)}
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

        {/* User */}
        <div className="border-t border-white/10 pt-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-chaama-gold/20 text-[13px] font-semibold text-chaama-gold">
              {initials}
            </div>

            <div className="min-w-0">
              <p className="truncate text-[13px] font-medium text-chaama-cream">
                {name}
              </p>

              <p className="text-[11px] text-chaama-cream/50">{user?.role || ""}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-2 text-[12px] text-chaama-cream/60 transition hover:text-chaama-gold"
          >
            <LogOut size={14} strokeWidth={1.8} />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* =====================================================
          MAIN
      ====================================================== */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* =================================================
            HEADER
        ================================================= */}
        <header className="sticky top-0 z-30 flex h-[65px] items-center justify-between border-b border-chaama-border bg-white px-4 sm:px-6 lg:px-10">
          {/* Hamburger */}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="flex h-9 w-9 items-center justify-center text-chaama-dark2 transition-colors hover:text-chaama-gold lg:hidden"
            aria-label="Ouvrir le menu"
          >
            <Menu size={21} strokeWidth={1.8} />
          </button>

          {/* Mobile logo */}
          <div className="ml-2 flex items-center lg:hidden">
            <span className="font-display text-[17px] tracking-wide text-chaama-dark">
              CHAAMA
            </span>
          </div>

          {/* Right header */}
          <div className="ml-auto flex items-center gap-3 sm:gap-5">
            {/* Notifications */}
            <NotificationDropdown />

            {/* Profile */}
            <NavLink
              to="/app/profile"
              className={({ isActive }) =>
                `flex items-center gap-2.5 border-l border-chaama-border pl-3 transition-colors sm:pl-5 ${
                  isActive
                    ? "text-chaama-dark2"
                    : "text-chaama-text hover:text-chaama-dark2"
                }`
              }
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-chaama-gold/15 text-[12px] font-semibold text-chaama-gold">
                {initials}
              </div>

              <span className="hidden text-[13px] font-medium sm:block">
                {name}
              </span>
            </NavLink>
          </div>
        </header>

        {/* =================================================
            PAGE CONTENT
        ================================================= */}
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
