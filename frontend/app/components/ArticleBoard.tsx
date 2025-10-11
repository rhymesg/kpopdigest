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
        const publishedLabel = Number.isNaN(published.getTime())
          ? 'Unknown date'
          : published.toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });
        return (
          <div key={article.id} className="card">
            <button className="title" onClick={() => toggle(article.id)}>
              <span className="source">[{article.source}]</span>
              <span>{mainTitle}</span>
              <span className="timestamp">{publishedLabel}</span>
            </button>
            {isExpanded && (
              <div className="details">
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
          align-items: center;
          gap: 12px;
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
        .source {
          color: #38bdf8;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 12px;
        }
        .timestamp {
          margin-left: auto;
          font-size: 13px;
          color: rgba(226, 232, 240, 0.6);
        }
        .details {
          padding: 16px 24px 24px;
          border-top: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(15, 23, 42, 0.4);
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
