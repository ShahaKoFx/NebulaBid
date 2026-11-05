import aiosqlite, os

DB_PATH = os.getenv("DB_PATH", "./nebula.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz',
                phone TEXT,
                pairs TEXT DEFAULT 'XAUUSD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def upsert_user(tg_id, **fields):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users(tg_id) VALUES(?)", (tg_id,))
        for k, v in fields.items():
            await db.execute(f"UPDATE users SET {k}=? WHERE tg_id=?", (v, tg_id))
        await db.commit()

async def get_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cur:
            return [dict(r) for r in await cur.fetchall()]
