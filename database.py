import aiosqlite
import os

DB_NAME = "jobfinder.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                url TEXT,
                city TEXT,
                query TEXT,
                category TEXT,
                filters TEXT,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration for existing DB matching the new schema if needed
        try:
            await db.execute("ALTER TABLE searches ADD COLUMN filters TEXT")
        except:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id TEXT PRIMARY KEY,
                search_id INTEGER,
                title TEXT,
                price TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(search_id) REFERENCES searches(id) ON DELETE CASCADE
            )
        """)
        await db.commit()

async def add_search(user_id, channel_id, url, city, query, category, filters_json):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO searches (user_id, channel_id, url, city, query, category, filters)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, channel_id, url, city, query, category, filters_json))
        await db.commit()
        return cursor.lastrowid

async def get_searches():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM searches") as cursor:
            return await cursor.fetchall()

async def get_user_searches(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM searches WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

async def remove_search(search_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM searches WHERE id = ? AND user_id = ?", (search_id, user_id))
        await db.commit()

async def offer_exists(offer_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM offers WHERE id = ?", (offer_id,)) as cursor:
            return await cursor.fetchone() is not None

async def add_offer(offer_id, search_id, title, price, url):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO offers (id, search_id, title, price, url)
            VALUES (?, ?, ?, ?, ?)
        """, (offer_id, search_id, title, price, url))
        await db.commit()

# Cleanup function to remove offers that are no longer relevant might be complex
# For now, we keep them to prevent re-alerting if they reappear or if the cleanup logic is buggy.
# We could delete old offers periodically.
