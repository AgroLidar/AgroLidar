import { ReactNode } from "react";

type BadgeVariant = "default" | "success" | "warning";

const variantStyles: Record<BadgeVariant, string> = {
  default: "border-white/20 bg-white/5 text-white/80",
  success: "border-emerald-300/40 bg-emerald-300/10 text-emerald-200",
  warning: "border-amber-300/40 bg-amber-300/10 text-amber-200"
};

type BadgeProps = {
  children: ReactNode;
  variant?: BadgeVariant;
};

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium tracking-wide ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
}
