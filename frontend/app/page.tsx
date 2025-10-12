import Link from 'next/link';

import { ArticleBoard } from './components/ArticleBoard';
import { fetchArticles } from '@/lib/articles';
import { fetchArtistsByViews } from '@/lib/artists';

const PAGE_SIZE = 20;

export const revalidate = 0;

export default async function HomePage() {
  const articles = await fetchArticles({ limit: PAGE_SIZE });
  const artists = await fetchArtistsByViews();

  return (
    <main>
      <header className="hero">
        <h1>K-pop Digest</h1>
        <p>Fresh Korean entertainment stories for global fans.</p>
        <p className="disclaimer">
          We respect the original content. Titles and summaries are rewritten, and every link sends you to the source.
        </p>
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
        <h2>K-pop news, blogs, and community photo posts in English</h2>
        <p>
          K-pop Digest curates idol coverage straight from the Korean sources fans rely on—Korean portals (Naver, Daum), entertainment newsrooms, and community/photo hubs like DCInside, Theqoo, Pann, and FMKorea. Every headline and summary is rewritten in clear English so you can preview the story before jumping to the original outlet. Follow the latest moves from BLACKPINK, BTS, IVE, aespa, Stray Kids, NewJeans, ENHYPEN, BABYMONSTER, and more.
        </p>
      </section>
    </main>
  );
}
