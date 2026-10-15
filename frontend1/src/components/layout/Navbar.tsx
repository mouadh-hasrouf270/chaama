import { ArrowUpRight, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  // Pages avec un Hero sombre derrière le Navbar
  const isDarkHeroPage = location.pathname === "/";

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 30);
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, [location.pathname]);

  const goToLogin = () => {
    setIsOpen(false);
    navigate("/auth/login");
  };

  const goToAppointment = () => {
    setIsOpen(false);
    navigate("/rendez-vous");
  };

  // Navbar sombre sur les pages claires
  const lightPage = !isDarkHeroPage;

  const navbarBackground = lightPage
    ? "bg-[#F7F6F2]/95 shadow-[0_1px_0_0_#E5E5DF] backdrop-blur-sm"
    : scrolled
      ? "bg-[#F7F6F2]/95 shadow-[0_1px_0_0_#E5E5DF] backdrop-blur-sm"
      : "bg-transparent";

  const navbarText = lightPage
    ? "text-[#193A42]"
    : scrolled
      ? "text-[#193A42]"
      : "text-white";

  const navLinksColor = lightPage
    ? "text-[#617982]"
    : scrolled
      ? "text-[#617982]"
      : "text-white/70";

  return (
    <header
      className={`fixed top-0 z-50 w-full transition-all duration-500 ${
        scrolled || lightPage ? "py-3" : "py-5"
      } ${navbarBackground}`}
    >
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between px-5 sm:px-7 lg:px-10">
        {/* Logo */}
        <button
          type="button"
          onClick={() => navigate("/")}
          className="flex shrink-0 items-center gap-2.5"
        >
          <span
            className={`grid h-7 w-7 place-items-center border text-[6px] font-semibold tracking-tight transition-colors ${
              lightPage || scrolled
                ? "border-[#C69A4A] text-[#193A42]"
                : "border-white/50 text-white"
            }`}
          >
            CHAAMA
          </span>

          <span
            className={`font-serif text-[15px] tracking-wide transition-colors ${
              lightPage || scrolled ? "text-[#193A42]" : "text-white"
            }`}
          >
            CHAAMA
          </span>
        </button>

        {/* Desktop Navigation */}
        <nav
          className={`hidden items-center gap-7 text-[11px] font-medium transition-colors lg:flex ${navLinksColor}`}
        >
          <a
            href="/#cabinet"
            className="transition-colors hover:text-[#C69A4A]"
          >
            Le cabinet
          </a>

          <a
            href="/#expertises"
            className="transition-colors hover:text-[#C69A4A]"
          >
            Expertises
          </a>

          <a
            href="/#valeurs"
            className="transition-colors hover:text-[#C69A4A]"
          >
            Valeurs
          </a>

          <a href="/contact" className="transition-colors hover:text-[#C69A4A]">
            Contact
          </a>
        </nav>

        {/* Desktop Buttons */}
        <div className="hidden shrink-0 items-center gap-5 lg:flex">
          <button
            type="button"
            onClick={goToLogin}
            className={`cursor-pointer text-[11px] font-semibold transition-colors ${
              lightPage || scrolled
                ? "text-[#193A42] hover:text-[#C69A4A]"
                : "text-white/80 hover:text-[#C69A4A]"
            }`}
          >
            Accès professionnel
          </button>

          <button
            type="button"
            onClick={goToAppointment}
            className="group flex cursor-pointer items-center gap-2 bg-[#C69A4A] px-4 py-2.5 text-[11px] font-semibold text-white transition-all hover:bg-[#B5893F] hover:shadow-lg"
          >
            Prendre rendez-vous
            <ArrowUpRight
              size={13}
              className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
            />
          </button>
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          aria-label={isOpen ? "Fermer le menu" : "Ouvrir le menu"}
          onClick={() => setIsOpen((prev) => !prev)}
          className={`lg:hidden ${
            lightPage || scrolled ? "text-[#193A42]" : "text-white"
          }`}
        >
          {isOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="absolute left-0 top-full w-full border-b border-[#D9DEDB] bg-[#F7F6F2] px-6 py-5 shadow-md lg:hidden">
          <nav className="flex flex-col gap-4 text-[13px] font-medium text-[#617982]">
            <a
              href="/#cabinet"
              onClick={() => setIsOpen(false)}
              className="transition-colors hover:text-[#C69A4A]"
            >
              Le cabinet
            </a>

            <a
              href="/#expertises"
              onClick={() => setIsOpen(false)}
              className="transition-colors hover:text-[#C69A4A]"
            >
              Expertises
            </a>

            <a
              href="/#valeurs"
              onClick={() => setIsOpen(false)}
              className="transition-colors hover:text-[#C69A4A]"
            >
              Valeurs
            </a>

            <a
              href="/contact"
              onClick={() => setIsOpen(false)}
              className="transition-colors hover:text-[#C69A4A]"
            >
              Contact
            </a>

            <button
              type="button"
              onClick={goToLogin}
              className="cursor-pointer text-left text-[#C69A4A] transition-colors hover:text-[#B5893F]"
            >
              Accès professionnel
            </button>

            <button
              type="button"
              onClick={goToAppointment}
              className="mt-1 bg-[#193A42] px-4 py-3 text-center font-semibold text-white transition-colors hover:bg-[#102F37]"
            >
              Prendre rendez-vous
            </button>
          </nav>
        </div>
      )}
    </header>
  );
};

export default Navbar;
