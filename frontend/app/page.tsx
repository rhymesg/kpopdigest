import Link from 'next/link';

import { ArticleBoard } from './components/ArticleBoard';
import { fetchArticles } from '@/lib/articles';
import { fetchArtistsByViews } from '@/lib/artists';
import { SITE_CONTENT } from '@/lib/content';

const PAGE_SIZE = 20;

export const revalidate = 0;

export default async function HomePage() {
  const articles = await fetchArticles({ limit: PAGE_SIZE });
  const artists = await fetchArtistsByViews();

  return (
    <main>
      <header className="hero">
        <h1>K-pop Digest</h1>
        <p>{SITE_CONTENT.tagline}</p>
        <nav>
          {artists.map((artist) => (
            <Link key={artist.slug} href={`/${artist.slug}`}>
              {artist.name}
            </Link>
          ))}
        </nav>
      </header>

      <section>
        <ArticleBoard initialArticles={articles} />
      </section>

      <section className="seo-blurb">
        <h2>K-pop news, blogs, and community updates</h2>
        <p>{SITE_CONTENT.description.main}</p>
      </section>

      <footer className="disclaimer">
        <p>{SITE_CONTENT.copyright}</p>
      </footer>
    </main>
  );
}
