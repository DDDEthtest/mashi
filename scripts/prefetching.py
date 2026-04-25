import asyncio
from data.postgres.postgres_manager import db_manager, Base
from data.remote.mashit_api import get_shop_list
from services.caching import fetch_and_cache_async

Base.metadata.create_all(db_manager.engine)


async def prefetch_async():
    limit = 20
    offset = 0
    has_more = True

    try:
        while has_more:
            print(f"Fetching page at offset {offset}...")

            # 1. Fetch the shop list (Sync API call -> Thread)
            shop_data = await asyncio.to_thread(get_shop_list, limit=limit, offset=offset)

            listings = shop_data.get("listings", [])
            pagination = shop_data.get("pagination", {})

            if not listings:
                break

            # 2. Create tasks for the async caching service
            tasks = []
            for item in listings:
                item_id = item.get("id")
                if item_id:
                    # NOTICE: We call it directly because it is already async!
                    tasks.append(fetch_and_cache_async(item_id))

            # 3. Run all caching tasks for this page in parallel
            if tasks:
                await asyncio.gather(*tasks)

            # 4. Handle pagination
            has_more = pagination.get("hasMore", False)
            offset += len(listings)
            print(f"✅ Processed {len(listings)} items. Total offset: {offset}")

    except Exception as e:
        print(f"❌ An error occurred during execution: {e}")
