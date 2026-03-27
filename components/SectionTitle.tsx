import { ReactNode } from "react";

type SectionTitleProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  align?: "left" | "center";
};

export function SectionTitle({ title, subtitle, align = "left" }: SectionTitleProps) {
  const alignment = align === "center" ? "text-center" : "text-left";

  return (
    <header className={`space-y-3 ${alignment}`}>
      <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h2>
      {subtitle ? <p className="text-sm text-white/75 sm:text-base">{subtitle}</p> : null}
    </header>
  );
}
