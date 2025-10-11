import Link from 'next/link';

import { ArticleBoard } from './components/ArticleBoard';
import { fetchArticles } from '@/lib/articles';
import { ARTISTS } from '@/lib/artists';

const PAGE_SIZE = 20;

export const revalidate = 0;

export default async function HomePage() {
  const articles = await fetchArticles({ limit: PAGE_SIZE });

  return (
    <main>
      <header className="hero">
        <h1>K-pop Digest</h1>
        <p>Freshly rewritten Korean entertainment stories for global fans.</p>
        <nav>
          <Link href="/">All</Link>
          {ARTISTS.map((artist) => (
            <Link key={artist.slug} href={`/${artist.slug}`}>
              {artist.name}
            </Link>
          ))}
        </nav>
      </header>

      <section>
        <ArticleBoard initialArticles={articles} />
      </section>
    </main>
  );
}
