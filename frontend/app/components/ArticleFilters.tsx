'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { ARTICLE_CATEGORIES, type ArticleCategory } from '@/lib/categories';

const ALL_VALUE = 'all';

interface ArticleFiltersProps {
  currentCategory?: ArticleCategory;
  currentSearch?: string;
}

export function ArticleFilters({ currentCategory, currentSearch }: ArticleFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [searchValue, setSearchValue] = useState(currentSearch ?? '');

  useEffect(() => {
    setSearchValue(currentSearch ?? '');
  }, [currentSearch]);

  const active = currentCategory ?? ALL_VALUE;

  const options = useMemo(() => [ALL_VALUE, ...ARTICLE_CATEGORIES], []);

  const buildTarget = (params: URLSearchParams) => {
    const query = params.toString();
    return query ? `${pathname}?${query}` : pathname;
  };

  const handleSelect = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === ALL_VALUE) {
      params.delete('category');
    } else {
      params.set('category', value);
    }
    const target = buildTarget(params);
    router.push(target, { scroll: false });
  };

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    const trimmed = searchValue.trim();
    if (trimmed) {
      params.set('search', trimmed);
    } else {
      params.delete('search');
    }
    const target = buildTarget(params);
    router.push(target, { scroll: false });
  };

  return (
    <div className="filters">
      <div className="category-toggle" role="group" aria-label="Filter by category">
        {options.map((option) => {
          const isActive = option === active;
          const label = option.toUpperCase();
          return (
            <button
              key={option}
              type="button"
              className={`category-toggle__button ${isActive ? 'is-active' : ''}`}
              onClick={() => handleSelect(option)}
              aria-pressed={isActive}
            >
              {label}
            </button>
          );
        })}
      </div>

      <form className="search" role="search" onSubmit={handleSearchSubmit}>
        <label htmlFor="article-search" className="visually-hidden">
          Search headlines
        </label>
        <input
          id="article-search"
          type="search"
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          placeholder="Search headlines"
        />
        <button type="submit">Search</button>
      </form>

      <style jsx>{`
        .filters {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          margin-top: 16px;
          align-items: center;
        }

        .category-toggle {
          display: inline-flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .category-toggle__button {
          border: 1px solid #cbd5f5;
          background: #eff6ff;
          color: #1e3a8a;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.08em;
          padding: 6px 14px;
          border-radius: 9999px;
          text-transform: uppercase;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .category-toggle__button:hover {
          background: #dbeafe;
        }

        .category-toggle__button.is-active {
          background: #1d4ed8;
          color: #ffffff;
          border-color: #1d4ed8;
          box-shadow: 0 0 0 2px rgba(29, 78, 216, 0.2);
        }

        .search {
          display: inline-flex;
          gap: 8px;
          align-items: center;
          padding: 4px;
          background: #f8fafc;
          border-radius: 9999px;
          border: 1px solid #cbd5f5;
        }

        .search input {
          border: none;
          background: transparent;
          padding: 6px 12px;
          min-width: 180px;
          font-size: 14px;
          outline: none;
        }

        .search button {
          border: none;
          background: #1d4ed8;
          color: #ffffff;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.06em;
          padding: 6px 14px;
          border-radius: 9999px;
          cursor: pointer;
          text-transform: uppercase;
        }

        .search button:hover {
          background: #1e40af;
        }

        .visually-hidden {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }
      `}</style>
    </div>
  );
}
