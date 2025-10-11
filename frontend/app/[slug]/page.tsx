import { notFound } from 'next/navigation';
import Link from 'next/link';

import { ArticleBoard } from '../components/ArticleBoard';
import { ARTISTS } from '@/lib/artists';
import { fetchArticles } from '@/lib/articles';

const PAGE_SIZE = 20;

export const revalidate = 0;

interface Props {
  params: { slug: string };
}

export default async function ArtistPage({ params }: Props) {
  const artist = ARTISTS.find((item) => item.slug === params.slug);
  if (!artist) {
    notFound();
  }

  const articles = await fetchArticles({ limit: PAGE_SIZE, artistSlug: artist.slug });

  return (
    <main>
      <header className="hero hero--artist">
        <h1>{artist.name}</h1>
        <p>Latest stories featuring {artist.name}. Tap a headline for the AI recap.</p>
        <nav>
          <Link href="/">← Back to all artists</Link>
        </nav>
      </header>

      <section>
        <ArticleBoard initialArticles={articles} artistSlug={artist.slug} />
      </section>

    </main>
  );
}
