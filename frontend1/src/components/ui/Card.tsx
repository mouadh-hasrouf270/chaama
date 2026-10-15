import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`border border-chaama-border bg-white ${className}`}>
      {children}
    </div>
  );
}
