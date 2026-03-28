import { getRequestConfig } from 'next-intl/server';

import en from '@/i18n/messages/en.json';
import es from '@/i18n/messages/es.json';

const MESSAGES = { en, es } as const;

export default getRequestConfig(async ({ locale }) => ({
  locale: locale === 'es' ? 'es' : 'en',
  messages: locale === 'es' ? MESSAGES.es : MESSAGES.en,
}));
