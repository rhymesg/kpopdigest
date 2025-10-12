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
            <button className="title" onClick={() => toggle(article.id)}>
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
                <a href={destination} target="_blank" rel="noreferrer">
                  <h4>{article.titleRaw}</h4>
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
          gap: 12px;
        }
        .card {
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          overflow: hidden;
        }
        .title {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 16px;
          background: none;
          border: none;
          color: inherit;
          font-size: 16px;
          font-weight: 600;
          text-align: left;
          cursor: pointer;
        }
        .title:hover {
          background: rgba(148, 163, 184, 0.08);
        }
        .meta-line {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 12px;
        }
        .headline {
          flex: 1 1 auto;
          padding-right: 4px;
        }
        .meta__source {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: rgba(148, 163, 184, 0.85);
        }
        .meta__source--news {
          color: #60a5fa;
        }
        .meta__source--blog {
          color: #34d399;
        }
        .meta__source--community {
          color: #fb7185;
        }
        .meta__source--etc {
          color: rgba(148, 163, 184, 0.85);
        }
        .meta-line .date {
          font-size: 12px;
          color: rgba(226, 232, 240, 0.6);
        }
        .details {
          padding: 16px 24px 24px;
          border-top: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(15, 23, 42, 0.4);
        }
        .meta-row {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }
        .pill {
          display: inline-flex;
          align-items: center;
          padding: 4px 10px;
          border-radius: 999px;
          font-size: 12px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .pill__category {
          background: rgba(56, 189, 248, 0.12);
          color: #38bdf8;
        }
        .pill__timestamp {
          background: rgba(148, 163, 184, 0.12);
          color: rgba(226, 232, 240, 0.75);
        }
        .details h4 {
          margin: 0 0 12px;
          font-size: 18px;
          color: #22d3ee;
        }
        .details p {
          margin: 0;
          font-size: 15px;
          line-height: 1.6;
          color: rgba(226, 232, 240, 0.92);
        }
        .load-more {
          margin: 24px auto 0;
          display: inline-flex;
          padding: 12px 32px;
          border-radius: 999px;
          border: none;
          background: linear-gradient(135deg, #14b8a6, #6366f1);
          color: #0f172a;
          font-weight: 600;
          cursor: pointer;
        }
        .load-more:disabled {
          opacity: 0.7;
          cursor: progress;
        }
      `}</style>
    </div>
  );
}
