import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'K-pop Digest',
  description:
    'Fresh K-pop news, blog recaps, and community photo posts rewritten in English for global fans. Discover daily idol headlines and summaries across BLACKPINK, BTS, IVE, Stray Kids, aespa, NewJeans, ENHYPEN, BABYMONSTER, and more.',
  keywords: [
    'K-pop news',
    'K-pop blog recaps',
    'K-pop community posts',
    'idol headlines',
    'BLACKPINK news',
    'BTS update',
    'IVE news',
    'aespa news',
    'Stray Kids news',
    'NewJeans news',
    'ENHYPEN news',
    'BABYMONSTER news',
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
