import logging
from pathlib import Path
from datetime import datetime
from .news_agent import NewsReport, Article

logger = logging.getLogger("agent.blog")

BLOG_DIR = Path(__file__).resolve().parent.parent / "blog"
OUTPUT_FILE = BLOG_DIR / "index.html"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rabbit Alert - Veille Lapin</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f0eb; color: #2d2a24; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  header {{ background: linear-gradient(135deg, #5b4033 0%, #8b6f5a 100%); color: #fff; padding: 40px 0 30px; text-align: center; }}
  header h1 {{ font-size: 2em; margin-bottom: 6px; }}
  header p {{ opacity: .85; font-size: .95em; }}
  .meta {{ text-align: center; color: #7a6b5e; font-size: .85em; margin: 12px 0 24px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: .75em; font-weight: 600; text-transform: uppercase; }}
  .badge-recall {{ background: #e74c3c; color: #fff; }}
  .badge-health {{ background: #2ecc71; color: #fff; }}
  .badge-news {{ background: #3498db; color: #fff; }}
  article {{ background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
  article h2 {{ font-size: 1.15em; margin-bottom: 6px; }}
  article h2 a {{ color: #2d2a24; text-decoration: none; }}
  article h2 a:hover {{ color: #5b4033; text-decoration: underline; }}
  article .source {{ font-size: .8em; color: #8b7f72; }}
  article .source span {{ color: #5b4033; font-weight: 600; }}
  article .desc {{ margin-top: 6px; font-size: .92em; color: #4a4238; }}
  article .date {{ font-size: .78em; color: #a09284; margin-top: 8px; }}
  footer {{ text-align: center; padding: 30px 0; color: #a09284; font-size: .82em; }}
  .empty {{ text-align: center; padding: 60px 20px; color: #8b7f72; }}
  @media (max-width: 600px) {{ header h1 {{ font-size: 1.5em; }} .container {{ padding: 12px; }} }}
</style>
</head>
<body>
<header>
  <div class="container">
    <h1>🐇 Rabbit Alert</h1>
    <p>Veille automatique : rappels produits & actualités lapin</p>
  </div>
</header>
<div class="container">
  <div class="meta">
    Dernière mise à jour : {generated_at} &middot; {count} article{count_plural}
  </div>
  {articles}
</div>
<footer>
  <div class="container">
    Généré automatiquement par Rabbit Alert Agent &middot; Sources : NewsAPI
  </div>
</footer>
</body>
</html>"""

ARTICLE_HTML = """<article>
  <span class="badge badge-{category}">{category_label}</span>
  <h2><a href="{url}" target="_blank" rel="noopener">{title}</a></h2>
  <div class="source">Source : <span>{source}</span> &middot; {date}</div>
  <div class="desc">{description}</div>
  {summary_block}
</article>"""

CATEGORY_LABELS = {
    "recall": "Rappel",
    "health": "Santé",
    "news": "News",
}


class BlogGenerator:
    def generate(self, report: NewsReport) -> Path:
        BLOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Génération du blog: %d articles", report.total_count)

        articles_html = ""
        for art in report.articles:
            cat_label = CATEGORY_LABELS.get(art.category, art.category)
            summary_block = ""
            if art.summary:
                summary_block = f'<div class="desc" style="margin-top:4px;font-style:italic;color:#6b6054;">{art.summary}</div>'

            try:
                dt = datetime.fromisoformat(art.published_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%d/%m/%Y")
            except Exception:
                date_str = art.published_at[:10] if art.published_at else ""

            articles_html += ARTICLE_HTML.format(
                category=art.category,
                category_label=cat_label,
                url=art.url,
                title=art.title,
                source=art.source,
                date=date_str,
                description=art.description,
                summary_block=summary_block,
            )

        if not articles_html:
            articles_html = '<div class="empty"><p>Aucun article trouvé pour le moment.</p></div>'

        generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")
        count = report.total_count
        html = TEMPLATE.format(
            generated_at=generated_at,
            count=count,
            count_plural="s" if count > 1 else "",
            articles=articles_html,
        )

        OUTPUT_FILE.write_text(html, encoding="utf-8")
        logger.info("Blog généré: %s", OUTPUT_FILE)
        return OUTPUT_FILE
