import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("agent.news")

NEWS_API_KEY_ENV = "NEWS_API_KEY"
NEWS_API_BASE = "https://newsapi.org/v2/everything"

@dataclass
class Article:
    title: str
    description: str
    url: str
    source: str
    published_at: str
    category: str = "news"
    summary: str = ""

@dataclass
class NewsReport:
    generated_at: str
    articles: List[Article] = field(default_factory=list)
    total_count: int = 0


class NewsAgent:
    def __init__(self):
        self.api_key = os.environ.get(NEWS_API_KEY_ENV, "")
        if not self.api_key:
            logger.warning("NEWS_API_KEY non définie — mode démo")

    async def run(self) -> NewsReport:
        logger.info("=== NEWS AGENT RUN ===")
        articles = await self._fetch_rabbit_news()
        report = NewsReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            articles=articles,
            total_count=len(articles),
        )
        logger.info("NewsAgent terminé: %d articles trouvés", len(articles))
        return report

    async def _fetch_rabbit_news(self) -> List[Article]:
        if not self.api_key:
            return self._demo_articles()

        keywords = [
            '"rabbit" OR "lapin" product recall',
            '"rabbit food" recall OR safety',
            '"lapin" rappel produit OR aliment',
            '"pet rabbit" health alert OR recall',
            '"rabbit feed" contamination OR recall',
        ]

        all_articles: List[Article] = []
        seen_urls = set()

        for query in keywords:
            try:
                articles = await self._fetch_newsapi(query)
                for a in articles:
                    if a.url not in seen_urls:
                        seen_urls.add(a.url)
                        all_articles.append(a)
            except Exception as e:
                logger.warning("Erreur pour query '%s': %s", query, e)

        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles[:50]

    async def _fetch_newsapi(self, query: str) -> List[Article]:
        import httpx

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(NEWS_API_BASE, params=params)

        if resp.status_code != 200:
            logger.warning("NewsAPI error %d: %s", resp.status_code, resp.text)
            return []

        data = resp.json()
        if data.get("status") != "ok":
            return []

        results = []
        for item in data.get("articles", []):
            article = Article(
                title=item.get("title", ""),
                description=item.get("description", "") or "",
                url=item.get("url", ""),
                source=item.get("source", {}).get("name", ""),
                published_at=item.get("publishedAt", ""),
                category=self._classify(item.get("title", ""), item.get("description", "")),
            )
            if article.title and article.url:
                results.append(article)
        return results

    def _classify(self, title: str, desc: str) -> str:
        text = (title + " " + desc).lower()
        recall_words = ["rappel", "recall", "alert", "withdrawn", "contamination",
                        "danger", "warning", "safety", "recal", "retrait"]
        if any(w in text for w in recall_words):
            return "recall"
        health_words = ["health", "santé", "vet", "veterinary", "disease",
                        "maladie", "care", "soin", "nutrition"]
        if any(w in text for w in health_words):
            return "health"
        return "news"

    def _demo_articles(self) -> List[Article]:
        return [
            Article(
                title="RAPPEL PRODUIT: Marque X pelleted rabbit food",
                description="Rappel de lots de granulés pour lapins en raison d'un taux de calcium trop élevé détecté lors de contrôles vétérinaires.",
                url="https://example.com/rappel-lapin-1",
                source="DGCCRF",
                published_at="2026-06-05T10:00:00Z",
                category="recall",
                summary="Rappel de granulés pour cause de calcium excessif.",
            ),
            Article(
                title="Nouvelle étude: l'alimentation du lapin domestique",
                description="Une étude CHUV 2025 révèle l'importance des fibres longues dans la prévention des troubles digestifs chez le lapin nain.",
                url="https://example.com/etude-lapin-2025",
                source="CHUV",
                published_at="2026-06-04T08:00:00Z",
                category="health",
                summary="Étude sur les fibres dans l'alimentation du lapin.",
            ),
            Article(
                title="Rappel de foin contaminé dans 3 départements",
                description="Du foin destiné aux rongeurs et lapins a été retiré de la vente pour suspicion de moisissures toxiques.",
                url="https://example.com/rappel-foin",
                source="RappelConso",
                published_at="2026-06-03T14:30:00Z",
                category="recall",
                summary="Foin retiré pour suspicion de moisissures.",
            ),
        ]
