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
        <div className="feedback-section">
          <span className="feedback-text">Any comment, feedback, or request?</span>
          <a className="feedback-button" href="mailto:contact@kpopdigest.com" target="_blank" rel="noopener noreferrer" aria-label="Send email">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <polyline points="22,6 12,13 2,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </a>
        </div>
      </footer>
    </main>
  );
}
