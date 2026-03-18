"""
Seed the bookmakers table with the 5 supported bookmakers.
Run this ONCE after database migration:

    cd backend
    python seed_bookmakers.py
"""
import asyncio
import json
import os

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.models.cricket import Bookmaker

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "data", "bookmaker_configs")

BOOKMAKERS = [
    {
        "name": "bet365",
        "display_name": "Bet365",
        "bookmaker_type": "bookmaker",
        "base_url": "https://www.bet365.com",
        "commission_pct": 0,
        "scrape_interval_seconds": 30,
    },
    {
        "name": "betfair",
        "display_name": "Betfair Exchange",
        "bookmaker_type": "exchange",
        "base_url": "https://www.betfair.com",
        "commission_pct": 5.0,
        "scrape_interval_seconds": 20,
    },
    {
        "name": "pinnacle",
        "display_name": "Pinnacle",
        "bookmaker_type": "bookmaker",
        "base_url": "https://www.pinnacle.com",
        "commission_pct": 0,
        "scrape_interval_seconds": 25,
    },
    {
        "name": "1xbet",
        "display_name": "1xBet",
        "bookmaker_type": "bookmaker",
        "base_url": "https://1xbet.com",
        "commission_pct": 0,
        "scrape_interval_seconds": 30,
    },
    {
        "name": "betway",
        "display_name": "Betway",
        "bookmaker_type": "bookmaker",
        "base_url": "https://www.betway.com",
        "commission_pct": 0,
        "scrape_interval_seconds": 30,
    },
]


async def seed():
    await init_db()

    async with AsyncSessionLocal() as session:
        for bk in BOOKMAKERS:
            existing = await session.execute(
                select(Bookmaker).where(Bookmaker.name == bk["name"])
            )
            if existing.scalar_one_or_none():
                print(f"  [skip] {bk['name']} already exists")
                continue

            bookmaker = Bookmaker(**bk)
            session.add(bookmaker)
            print(f"  [add]  {bk['name']}")

        await session.commit()
        print("\nBookmakers seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
