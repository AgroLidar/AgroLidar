import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin();

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  cacheComponents: true,
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, s-maxage=300, stale-while-revalidate=86400' },
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
