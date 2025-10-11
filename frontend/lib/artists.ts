import { pool } from './db';

export interface ArtistDefinition {
  slug: string;
  name: string;
}

export interface ArtistInfo extends ArtistDefinition {
  pageViews: number;
}

const DEFINITIONS: ArtistDefinition[] = [
  { slug: 'blackpink', name: 'BLACKPINK' },
  { slug: 'bts', name: 'BTS' },
  { slug: 'ive', name: 'IVE' },
  { slug: 'straykids', name: 'Stray Kids' },
  { slug: 'aespa', name: 'aespa' },
  { slug: 'babymonster', name: 'BABYMONSTER' },
  { slug: 'newjeans', name: 'NewJeans' },
  { slug: 'enhypen', name: 'ENHYPEN' },
];

export function getArtistDefinitions(): ArtistDefinition[] {
  return DEFINITIONS;
}

export function getArtistBySlug(slug: string): ArtistDefinition | undefined {
  return DEFINITIONS.find((artist) => artist.slug === slug);
}

export async function fetchArtistsByViews(): Promise<ArtistInfo[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(
      `
      SELECT ar."slug", ar."name", COALESCE(am."pageViews", 0) AS views
      FROM "Artist" ar
      LEFT JOIN "ArtistMetrics" am ON am."artistId" = ar."id"
      ORDER BY views DESC, ar."name" ASC
      `,
    );

    const metrics = new Map<string, number>();
    for (const row of result.rows) {
      metrics.set(row.slug, Number(row.views) || 0);
    }

    return DEFINITIONS.map((def) => ({
      ...def,
      pageViews: metrics.get(def.slug) ?? 0,
    })).sort((a, b) => {
      if (b.pageViews !== a.pageViews) return b.pageViews - a.pageViews;
      return a.name.localeCompare(b.name);
    });
  } finally {
    client.release();
  }
}
