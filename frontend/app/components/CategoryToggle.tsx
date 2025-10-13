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
          gap: 8px;
          margin-top: 16px;
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
      `}</style>
    </div>
  );
}
