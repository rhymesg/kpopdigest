import { notFound } from 'next/navigation';
import Link from 'next/link';

import { ArticleBoard } from '../components/ArticleBoard';
import { ArticleFilters } from '../components/ArticleFilters';
import { fetchArticles } from '@/lib/articles';
import { getArtistBySlug } from '@/lib/artists';
import { incrementArtistPageView } from '@/lib/metrics';
import { SITE_CONTENT } from '@/lib/content';
import { normalizeCategory } from '@/lib/categories';

const PAGE_SIZE = 20;

export const revalidate = 0;

interface Props {
  params: { slug: string };
  searchParams?: Record<string, string | string[] | undefined>;
}

export default async function ArtistPage({ params, searchParams }: Props) {
  const artist = getArtistBySlug(params.slug);
  if (!artist) {
    notFound();
  }

  await incrementArtistPageView(artist.slug);
  const categoryParam = Array.isArray(searchParams?.category)
    ? searchParams?.category[0]
    : searchParams?.category;
  const category = normalizeCategory(categoryParam);
  const searchParam = Array.isArray(searchParams?.search)
    ? searchParams?.search[0]
    : searchParams?.search;
  const search = searchParam?.trim() ? searchParam.trim() : undefined;

  const articles = await fetchArticles({
    limit: PAGE_SIZE,
    artistSlug: artist.slug,
    category,
    search,
  });

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
        <div className="articles-header">
          <ArticleFilters currentCategory={category} currentSearch={search} />
        </div>
        <ArticleBoard
          initialArticles={articles}
          artistSlug={artist.slug}
          category={category}
          search={search}
        />
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
