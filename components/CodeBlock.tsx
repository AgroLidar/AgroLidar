import { ReactNode } from "react";

type CodeBlockProps = {
  children: ReactNode;
};

export function CodeBlock({ children }: CodeBlockProps) {
  return (
    <pre className="overflow-x-auto rounded-xl border border-slate-700/80 bg-slate-950 p-4 font-mono text-xs text-emerald-200 shadow-inner sm:text-sm">
      <code>{children}</code>
    </pre>
  );
}
