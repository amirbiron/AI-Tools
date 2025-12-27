"""
Mongo Distributed Lock – מניעת telegram.error.Conflict

רעיון:
- קולקציה אחת bot_locks
- SERVICE_ID מי נועל, INSTANCE_ID מי מריץ
- לוק יש expiresAt + TTL לנעילות יתומות
"""

import os, asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient, ReturnDocument

URI = os.getenv("MONGODB_URI")
SERVICE_ID = os.getenv("SERVICE_ID", "codebot-prod")
INSTANCE_ID = os.getenv("RENDER_INSTANCE_ID", "local")
LEASE = int(os.getenv("LOCK_LEASE_SECONDS", "60"))
RETRY = int(os.getenv("LOCK_RETRY_SECONDS", "20"))

col = MongoClient(URI)["codebot"]["bot_locks"]
col.create_index("expiresAt", expireAfterSeconds=0)

async def acquire_lock():
    """רכישת לוק – חוזר רק כשהאינסטנס הוא הבעלים."""
    while True:
        now = datetime.utcnow()
        exp = now + timedelta(seconds=LEASE)

        doc = col.find_one_and_update(
            {
                "_id": SERVICE_ID,
                "$or": [
                    {"expiresAt": {"$lte": now}},   # תפוס אבל פג תוקף
                    {"owner": INSTANCE_ID},         # חידוש
                ],
            },
            {"$set": {"owner": INSTANCE_ID, "expiresAt": exp, "updatedAt": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        if doc["owner"] == INSTANCE_ID:
            print(f"✅ lock by {INSTANCE_ID} until {exp}")
            return

        print(f"🔒 held by {doc['owner']} – retry in {RETRY}s")
        await asyncio.sleep(RETRY)

async def heartbeat():
    """שמירת בעלות – רענון expiresAt. מאבד? יוצא."""
    interval = max(5, int(LEASE * 0.4))

    while True:
        await asyncio.sleep(interval)
        now = datetime.utcnow()
        exp = now + timedelta(seconds=LEASE)

        doc = col.find_one_and_update(
            {"_id": SERVICE_ID, "owner": INSTANCE_ID},
            {"$set": {"expiresAt": exp, "updatedAt": now}},
            return_document=ReturnDocument.AFTER,
        )

        if not doc:
            print("⚠️ lost lock – exit")
            os._exit(0)

        print(f"💓 heartbeat → {exp}")

async def main():
    await acquire_lock()
    asyncio.create_task(heartbeat())

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())