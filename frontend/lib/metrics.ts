import { pool } from './db';

export async function incrementArtistPageView(slug: string): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query(
      `
      INSERT INTO "ArtistMetrics" ("artistId", "pageViews", "updatedAt")
      SELECT "id", 1, NOW()
      FROM "Artist"
      WHERE "slug" = $1
      ON CONFLICT ("artistId") DO UPDATE
        SET "pageViews" = "ArtistMetrics"."pageViews" + 1,
            "updatedAt" = NOW()
      `,
      [slug],
    );
  } finally {
    client.release();
  }
}
