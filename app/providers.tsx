"use client";

import { NextIntlClientProvider } from "next-intl";
import { useMemo } from "react";

import en from "@/i18n/messages/en.json";

export function Providers({ children }: { children: React.ReactNode }): React.ReactElement {
  const messages = useMemo(() => en, []);
  return (
    <NextIntlClientProvider locale="en" messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
