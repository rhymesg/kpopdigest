import { notFound } from 'next/navigation';
import Link from 'next/link';

import { ArticleBoard } from '../components/ArticleBoard';
import { fetchArticles } from '@/lib/articles';
import { getArtistBySlug } from '@/lib/artists';
import { incrementArtistPageView } from '@/lib/metrics';

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
        <p>Fresh Korean entertainment stories for global fans.</p>
        <p className="disclaimer">
          We respect the original content. Titles and summaries are rewritten, and every link sends you to the source.
        </p>
        <nav>
          <Link href="/">← Back to all artists</Link>
        </nav>
      </header>

      <section>
        <ArticleBoard initialArticles={articles} artistSlug={artist.slug} />
      </section>

      <section className="seo-blurb">
        <h2>{artist.name} news, blogs, and community updates</h2>
        <p>
          We translate and polish Korean-language coverage about {artist.name} from the same places domestic fans read—Korean portals (Naver, Daum), blogger recaps, and community/photo feeds like DCInside, Theqoo, Pann, and Instiz—so global supporters can skim the highlights before visiting the original story.
        </p>
      </section>

    </main>
  );
}
