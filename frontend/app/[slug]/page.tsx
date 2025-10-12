import { notFound } from 'next/navigation';
import Link from 'next/link';

import { ArticleBoard } from '../components/ArticleBoard';
import { fetchArticles } from '@/lib/articles';
import { getArtistBySlug } from '@/lib/artists';
import { incrementArtistPageView } from '@/lib/metrics';
import { SITE_CONTENT } from '@/lib/content';

const PAGE_SIZE = 20;

export const revalidate = 0;

interface Props {
  params: { slug: string };
}

export default async function ArtistPage({ params }: Props) {
  const artist = getArtistBySlug(params.slug);
  if (!artist) {
    notFound();
  }

  await incrementArtistPageView(artist.slug);
  const articles = await fetchArticles({ limit: PAGE_SIZE, artistSlug: artist.slug });

  return (
    <main>
      <header className="hero hero--artist">
        <h1>{artist.name}</h1>
        <p>{SITE_CONTENT.tagline}</p>
        <nav>
          <Link href="/">← Back to all artists</Link>
        </nav>
      </header>

      <section>
        <ArticleBoard initialArticles={articles} artistSlug={artist.slug} />
      </section>

      <section className="seo-blurb">
        <h2>{artist.name} news, blogs, and community updates</h2>
        <p>{SITE_CONTENT.description.main}</p>
      </section>

      <footer className="disclaimer">
        <p>{SITE_CONTENT.copyright}</p>
      </footer>
    </main>
  );
}
