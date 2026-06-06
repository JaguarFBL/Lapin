#!/usr/bin/env python3
"""
Rabbit Alert Agent — Script à scheduler (Task Scheduler / cron).
Usage : python run_agent.py

Prérequis : définir la variable d'environnement NEWS_API_KEY
(optionnelle — sans, le mode démo génère des exemples)
"""
import asyncio
import logging
import sys

sys.path.insert(0, ".")

from app.agents.news_agent import NewsAgent
from app.agents.blog_generator import BlogGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_agent")


async def main():
    logger.info("=== Rabbit Alert Agent ===")
    agent = NewsAgent()
    report = await agent.run()
    generator = BlogGenerator()
    path = generator.generate(report)
    logger.info("Blog mis à jour : %s (%d articles)", path, report.total_count)
    return path


if __name__ == "__main__":
    path = asyncio.run(main())
    print(f"\nBlog genere : {path}")
