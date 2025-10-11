import type { MetadataRoute } from 'next';

import { ARTISTS } from '@/lib/artists';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://kpopdigest.com';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date().toISOString();

  const artistEntries = ARTISTS.map((artist) => ({
    url: `${BASE_URL}/${artist.slug}`,
    lastModified: now,
    changeFrequency: 'hourly' as const,
    priority: 0.8,
  }));

  return [
    {
      url: `${BASE_URL}/`,
      lastModified: now,
      changeFrequency: 'hourly',
      priority: 1,
    },
    ...artistEntries,
  ];
}
