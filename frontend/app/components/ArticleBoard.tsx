'use client';

import { useState } from 'react';

import type { ArticleRow } from '@/lib/articles';

interface ArticleBoardProps {
  initialArticles: ArticleRow[];
  artistSlug?: string;
}

const PAGE_SIZE = 20;

export function ArticleBoard({ initialArticles, artistSlug }: ArticleBoardProps) {
  const [articles, setArticles] = useState(initialArticles);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(initialArticles.length === PAGE_SIZE);

  const loadMore = async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        offset: String(articles.length),
        limit: String(PAGE_SIZE),
      });
      if (artistSlug) params.set('slug', artistSlug);
      const res = await fetch(`/api/articles?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to load more articles');
      const data = await res.json();
      setArticles((prev) => [...prev, ...data.articles]);
      setHasMore(data.hasMore);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggle = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="board">
      {articles.map((article) => {
        const isExpanded = expandedId === article.id;
        const mainTitle = article.title ?? article.titleRaw;
        const destination = article.originalUrl;
        const published = new Date(article.publishedAt);
        const categoryClass = `meta__source meta__source--${article.category || 'default'}`;
        const publishedDateLabel = Number.isNaN(published.getTime())
          ? 'Unknown date'
          : published.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            });
        return (
          <div key={article.id} className="card">
            <button className={`title ${isExpanded ? 'expanded' : ''}`} onClick={() => toggle(article.id)}>
              <div className="meta-line">
                <span className={categoryClass}>{article.source}</span>
                <span className="date">{publishedDateLabel}</span>
              </div>
              <span className="headline">{mainTitle}</span>
            </button>
            {isExpanded && (
              <div className="details">
                <div className="meta-row">
                  <span className="pill pill__category">{article.category}</span>
                  <span className="pill pill__timestamp">
                    {Number.isNaN(published.getTime())
                      ? 'Unknown time'
                      : published.toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          timeZone: 'Asia/Seoul',
                        }) + ' KST'}
                  </span>
                </div>
                <a href={destination} target="_blank" rel="noreferrer" className="original-link">
                  <h4>{article.titleRaw} <span className="external-icon">⧉</span></h4>
                </a>
                {article.summary ? (
                  <p>{article.summary}</p>
                ) : (
                  <p>No summary available.</p>
                )}
              </div>
            )}
          </div>
        );
      })}

      {hasMore && (
        <button className="load-more" onClick={loadMore} disabled={isLoading}>
          {isLoading ? 'Loading…' : 'Load more'}
        </button>
      )}

      <style jsx>{`
        .board {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          overflow: hidden;
          box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
          transition: all 0.2s ease;
        }
        .card:hover {
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          transform: translateY(-1px);
        }
        .title {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 20px;
          background: none;
          border: none;
          color: #1e293b;
          font-size: 16px;
          font-weight: 600;
          text-align: left;
          cursor: pointer;
          position: relative;
        }
        .title:hover {
          background: #f8fafc;
        }
        .title::after {
          content: '▼';
          position: absolute;
          right: 20px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 12px;
          color: #94a3b8;
          transition: transform 0.2s ease;
        }
        .title:hover::after {
          color: #64748b;
        }
        .title.expanded::after {
          transform: translateY(-50%) rotate(180deg);
          color: #64748b;
        }
        .meta-line {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 12px;
        }
        .headline {
          flex: 1 1 auto;
          padding-right: 32px;
          line-height: 1.5;
        }
        .meta__source {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 4px 8px;
          border-radius: 6px;
          background: #f1f5f9;
          color: #64748b;
        }
        .meta__source--news {
          background: #dbeafe;
          color: #1d4ed8;
        }
        .meta__source--blog {
          background: #d1fae5;
          color: #047857;
        }
        .meta__source--community {
          background: #fce7f3;
          color: #be185d;
        }
        .meta__source--etc {
          background: #f1f5f9;
          color: #64748b;
        }
        .meta-line .date {
          font-size: 12px;
          color: #94a3b8;
          font-weight: 500;
        }
        .details {
          padding: 20px 24px 24px;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }
        .meta-row {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }
        .pill {
          display: inline-flex;
          align-items: center;
          padding: 6px 12px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .pill__category {
          background: #f1f5f9;
          color: #64748b;
          border: 1px solid #e2e8f0;
        }
        .pill__timestamp {
          background: #f1f5f9;
          color: #64748b;
          border: 1px solid #e2e8f0;
        }
        .original-link {
          display: block;
          text-decoration: none;
          color: #3b82f6;
          transition: color 0.2s ease;
        }
        .original-link:hover {
          color: #1d4ed8;
          text-decoration: underline;
        }
        .details h4 {
          margin: 0 0 16px;
          font-size: 18px;
          font-weight: 600;
          color: inherit;
          line-height: 1.4;
        }
        .external-icon {
          font-size: 14px;
          color: #94a3b8;
          margin-left: 6px;
          transition: color 0.2s ease;
        }
        .original-link:hover .external-icon {
          color: #1d4ed8;
        }
        .details p {
          margin: 0;
          font-size: 15px;
          line-height: 1.6;
          color: #475569;
        }
        .load-more {
          margin: 32px auto 0;
          display: inline-flex;
          padding: 14px 28px;
          border-radius: 12px;
          border: 2px solid #e2e8f0;
          background: #ffffff;
          color: #475569;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        .load-more:hover {
          background: #3b82f6;
          color: #ffffff;
          border-color: #3b82f6;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px 0 rgba(59, 130, 246, 0.3);
        }
        .load-more:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
          box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        .load-more:disabled:hover {
          background: #ffffff;
          color: #475569;
          border-color: #e2e8f0;
        }
      `}</style>
    </div>
  );
}
