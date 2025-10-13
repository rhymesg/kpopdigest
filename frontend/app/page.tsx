import Link from 'next/link';

import { ArticleBoard } from './components/ArticleBoard';
import { ArticleFilters } from './components/ArticleFilters';
import { fetchArticles } from '@/lib/articles';
import { fetchArtistsByViews } from '@/lib/artists';
import { SITE_CONTENT } from '@/lib/content';
import { normalizeCategory } from '@/lib/categories';

const PAGE_SIZE = 20;

export const revalidate = 0;

interface HomePageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const categoryParam = Array.isArray(searchParams?.category)
    ? searchParams?.category[0]
    : searchParams?.category;
  const category = normalizeCategory(categoryParam);
  const searchParam = Array.isArray(searchParams?.search)
    ? searchParams?.search[0]
    : searchParams?.search;
  const search = searchParam?.trim() ? searchParam.trim() : undefined;

  const articles = await fetchArticles({ limit: PAGE_SIZE, category, search });
  const artists = await fetchArtistsByViews();

  return (
    <main>
      <header className="hero">
        <h1>K-pop Digest</h1>
        <p>{SITE_CONTENT.tagline}</p>
        <nav className="hero-nav">
          {artists.map((artist) => (
            <Link key={artist.slug} href={`/${artist.slug}`}>
              {artist.name}
            </Link>
          ))}
        </nav>
      </header>

      <section>
        <ArticleFilters currentCategory={category} currentSearch={search} />
        <ArticleBoard initialArticles={articles} category={category} search={search} />
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
