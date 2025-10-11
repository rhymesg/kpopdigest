"""End-to-end helpers to fetch articles and run them through the LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence, Tuple

from .article_models import ArticleOriginal
from .chatgpt_client import ChatGPTClient, ChatGPTRewriteError
from .daum_api import fetch_daum_web
from .llm_models import ChatGPTRewriteOutput
from .naver_api import fetch_naver_news

SupportedAPI = Literal["naver", "daum"]


class PipelineError(RuntimeError):
    """Raised when the fetch → rewrite pipeline fails."""


@dataclass(slots=True)
class RewriteResult:
    article: ArticleOriginal
    rewrite: ChatGPTRewriteOutput


def _fetch_articles(api: SupportedAPI, query: str, *, artist: str, limit: int) -> list[ArticleOriginal]:
    if limit <= 0:
        return []

    if api == "naver":
        return fetch_naver_news(query, artist=artist, display=limit)[:limit]
    if api == "daum":
        return fetch_daum_web(query, artist=artist, size=limit)[:limit]

    raise PipelineError(f"Unsupported API: {api}")


def fetch_and_rewrite(
    api: SupportedAPI,
    query: str,
    *,
    artist: str,
    limit: int,
    model: str = "gpt-5-mini",
) -> Tuple[Sequence[ArticleOriginal], Sequence[ChatGPTRewriteOutput]]:
    """Fetch articles from the chosen API and rewrite them via ChatGPT."""

    print(f"[pipeline] Fetching up to {limit} '{api}' results for artist '{artist}' and query '{query}'...")
    articles = _fetch_articles(api, query, artist=artist, limit=limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return articles, []

    client = ChatGPTClient(model=model)
    print(f"[pipeline] Running rewrites with model '{model}'...")
    rewrites: list[ChatGPTRewriteOutput] = []
    total = min(len(articles), limit)
    for index, article in enumerate(articles[:limit], start=1):
        print(
            f"[pipeline] ({index}/{total}) {article.source} | {article.title_original[:60]}"
        )
        try:
            rewrite = client.rewrite(article)
        except ChatGPTRewriteError as exc:
            raise PipelineError(f"LLM rewrite failed for {article.original_url}: {exc}") from exc
        rewrites.append(rewrite)
    print("[pipeline] Completed rewrites.")
    return articles, rewrites
