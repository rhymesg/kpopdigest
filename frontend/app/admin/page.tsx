import { cookies } from 'next/headers';
import type { Metadata } from 'next';

import { ArticleBoard } from '../components/ArticleBoard';
import { ArticleFilters } from '../components/ArticleFilters';
import { AdminLoginForm } from './AdminLoginForm';
import { AdminLogoutButton } from './AdminLogoutButton';
import { isAdminAuthenticated } from '@/lib/adminAuth';
import { fetchArticlesWithHighlights } from '@/lib/articles';
import { normalizeCategory } from '@/lib/categories';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';

export const revalidate = 0;

export const metadata: Metadata = {
  title: 'Admin | K-pop Digest',
  robots: {
    index: false,
    follow: false,
  },
};

interface AdminPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default async function AdminPage({ searchParams }: AdminPageProps) {
  const isAuthenticated = isAdminAuthenticated(cookies());

  if (!isAuthenticated) {
    return (
      <main>
        <header className="hero">
          <h1>Admin</h1>
        </header>
        <AdminLoginForm />
      </main>
    );
  }

  const categoryParam = Array.isArray(searchParams?.category)
    ? searchParams?.category[0]
    : searchParams?.category;
  const category = normalizeCategory(categoryParam);
  const searchParam = Array.isArray(searchParams?.search)
    ? searchParams?.search[0]
    : searchParams?.search;
  const search = searchParam?.trim() ? searchParam.trim() : undefined;

  const { articles, featuredArticles } = await fetchArticlesWithHighlights({
    limit: DEFAULT_PAGE_SIZE,
    category,
    search,
  });

  return (
    <main>
      <header className="hero admin-hero">
        <h1>Admin</h1>
        <AdminLogoutButton />
      </header>

      <section>
        <ArticleFilters currentCategory={category} currentSearch={search} />
        <ArticleBoard
          initialArticles={articles}
          featuredArticles={featuredArticles}
          category={category}
          search={search}
          adminMode
        />
      </section>
    </main>
  );
}
