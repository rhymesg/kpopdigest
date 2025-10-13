'use client';

import { useMemo } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { ARTICLE_CATEGORIES, type ArticleCategory } from '@/lib/categories';

const ALL_VALUE = 'all';

interface CategoryToggleProps {
  currentCategory?: ArticleCategory;
}

export function CategoryToggle({ currentCategory }: CategoryToggleProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const active = currentCategory ?? ALL_VALUE;

  const options = useMemo(
    () => [ALL_VALUE, ...ARTICLE_CATEGORIES],
    [],
  );

  const handleSelect = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === ALL_VALUE) {
      params.delete('category');
    } else {
      params.set('category', value);
    }
    const query = params.toString();
    const target = query ? `${pathname}?${query}` : pathname;
    router.push(target, { scroll: false });
  };

  return (
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

      <style jsx>{`
        .category-toggle {
          display: inline-flex;
          gap: 4px;
          flex-wrap: wrap;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 6px;
          box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        }

        .category-toggle__button {
          border: none;
          background: transparent;
          color: #64748b;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.04em;
          padding: 10px 16px;
          border-radius: 12px;
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
      `}</style>
    </div>
  );
}
