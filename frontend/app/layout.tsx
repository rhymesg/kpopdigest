import './globals.css';
import type { Metadata } from 'next';
import { Analytics } from '@vercel/analytics/next';

export const metadata: Metadata = {
  title: 'K-pop Digest | K-pop News in English & Translated Korean Blogs',
  description:
    'K-pop Digest delivers kpop news in english every day by translating verified Korean newsrooms, idol blogs, and community forums. Find kpop translated korean news, kpop translated korean blogs, and kpop korean community posts in english for artists like BLACKPINK, BTS, IVE, Stray Kids, aespa, NewJeans, ENHYPEN, and BABYMONSTER.',
  keywords: [
    'kpop news in english',
    'kpop translated korean news',
    'kpop blogs in english',
    'kpop translated korean blogs',
    'kpop korean online forum',
    'kpop korean community posts english',
    'BLACKPINK news in English',
    'BTS updates',
    'K-pop translation site',
  ],
  openGraph: {
    title: 'K-pop Digest | K-pop News in English & Translated Korean Blogs',
    description:
      'Stay current with kpop news in english, translated Korean blogs, and rewritten community posts from DCInside, Theqoo, Pann, and more on K-pop Digest.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'K-pop Digest | K-pop News in English',
    description:
      'Daily kpop news in english with translated Korean articles, blogs, and community forum highlights for global fans.',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <link rel="manifest" href="/site.webmanifest" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
