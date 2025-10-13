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

      <div className="search-wrapper">
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
          <button type="submit" aria-label="Search">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </form>
      </div>

      <style jsx>{`
        .filters {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
          justify-content: space-between;
          width: 100%;
          margin: 8px 0 12px;
        }

        .category-toggle {
          display: inline-flex;
          gap: 4px;
          flex-wrap: wrap;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
          padding: 4px;
          box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.08), 0 1px 1px 0 rgba(0, 0, 0, 0.04);
        }

        .category-toggle__button {
          border: none;
          background: transparent;
          color: #64748b;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.04em;
          padding: 7px 13px;
          border-radius: 10px;
          text-transform: uppercase;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
        }

        .category-toggle__button:hover {
          background: #f8fafc;
          color: #475569;
        }

        .category-toggle__button.is-active {
          background: #3b82f6;
          color: #ffffff;
          box-shadow: 0 2px 4px 0 rgba(59, 130, 246, 0.3);
        }

        .category-toggle__button.is-active:hover {
          background: #2563eb;
        }

        .search {
          display: inline-flex;
          align-items: center;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 3px 3px 3px 10px;
          box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.06);
          transition: all 0.2s ease;
          min-height: 32px;
          min-width: 200px;
        }

        .search:focus-within {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .search input {
          border: none;
          background: transparent;
          padding: 4px 0;
          min-width: 160px;
          font-size: 13px;
          color: #1e293b;
          outline: none;
          flex: 1;
        }

        .search input::placeholder {
          color: #94a3b8;
        }

        .search-wrapper {
          margin-left: auto;
          display: flex;
        }

        .search button {
          border: none;
          background: #3b82f6;
          color: #ffffff;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-left: 8px;
          flex-shrink: 0;
        }

        .search button:hover {
          background: #2563eb;
          box-shadow: 0 2px 4px 0 rgba(59, 130, 246, 0.3);
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

        @media (max-width: 640px) {
          .filters {
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
          }

          .category-toggle {
            justify-content: flex-start;
          }

          .search-wrapper {
            margin-left: 0;
            width: auto;
          }

          .search {
            justify-content: flex-start;
            width: auto;
          }

          .search input {
            min-width: 0;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
