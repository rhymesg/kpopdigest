import Link from 'next/link';

import { ArticleBoard } from './components/ArticleBoard';
import { CategoryToggle } from './components/CategoryToggle';
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

  const articles = await fetchArticles({ limit: PAGE_SIZE, category });
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
        <div className="articles-header">
          <CategoryToggle currentCategory={category} />
        </div>
        <ArticleBoard initialArticles={articles} category={category} />
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
