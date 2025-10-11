import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'K-pop Digest',
  description: 'Latest K-pop news recaps rewritten for international fans.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
