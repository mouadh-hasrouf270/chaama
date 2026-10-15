import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "gold" | "dark" | "outline";
  className?: string;
}

const Button = ({
  children,
  href,
  onClick,
  disabled = false,
  variant = "gold",
  className = "",
}: ButtonProps) => {
  const base =
    "inline-flex items-center justify-center gap-3 px-5 py-3 text-xs tracking-wide transition-all duration-300";

  const variants = {
    gold: "bg-[#c69a4a] text-white hover:bg-[#b58a3f]",
    dark: "bg-[#193a42] text-white hover:bg-[#102f37]",
    outline:
      "border border-[#193a42]/30 text-[#193a42] hover:bg-[#193a42] hover:text-white",
  };

  const content = (
    <>
      {children}
      <ChevronRight size={14} />
    </>
  );

  if (href) {
    return (
      <a href={href} className={`${base} ${variants[variant]} ${className}`}>
        {content}
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${
        disabled ? "cursor-not-allowed opacity-50" : ""
      } ${className}`}
    >
      {content}
    </button>
  );
};

export default Button;
