import { Lock } from "lucide-react";
import { Link } from "react-router-dom";
const Footer = () => {
  return (
    <footer className="bg-[var(--chaama-dark-2)] px-6 py-12 lg:px-10">
      {" "}
      <div className="mx-auto flex max-w-[1200px] flex-col items-center justify-between gap-6 lg:flex-row">
        {" "}
        {/* Logo */}{" "}
        <div className="flex items-center gap-2.5">
          {" "}
          <span className="grid h-7 w-7 place-items-center border border-[var(--chaama-gold)] text-[6px] font-semibold text-[var(--chaama-gold)]">
            {" "}
            CHAAMA{" "}
          </span>{" "}
          <span className="font-display text-[15px] text-[var(--chaama-cream)]">
            {" "}
            CHAAMA{" "}
          </span>{" "}
        </div>{" "}
        {/* Copyright */}{" "}
        <p className="text-[10px] text-[var(--chaama-green)]">
          {" "}
          © 2026 CHAAMA — Cabinet d’avocats. Tous droits réservés.{" "}
        </p>{" "}
        {/* Professional access */}{" "}
        <Link
          to="/professional-access"
          className="cursor-pointer text-[10px] font-semibold uppercase tracking-wider text-[var(--chaama-green)] transition-colors duration-300 hover:text-[var(--chaama-gold)]"
        >
          {" "}
          Accès professionnel <Lock size={10} className="ml-1 inline" />{" "}
        </Link>{" "}
      </div>{" "}
    </footer>
  );
};
export default Footer;
