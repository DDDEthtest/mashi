import asyncio
from data.postgres.daos.image_dao import ImageDao
from data.remote.images_api import ImagesApi
from data.remote.mashi_api import MashiApi
from data.remote.mashit_api import MashitApi

class CachingService:
    _instance = None

    def __init__(self):
        # Initializing the APIs/DAOs
        self._mashi_api = MashiApi()
        self._mashit_api = MashitApi()
        self._image_dao = ImageDao()
        self._images_api = ImagesApi()
        self.gateway = "https://ipfs.filebase.io/ipfs/"

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _format_link(self, uri: str) -> str:
        if not uri or not uri.startswith("ipfs://"):
            return uri
        return uri.replace("ipfs://", self.gateway)

    async def _cache(self, url: str):

        """
        Helper to handle the logic.
        Note: Using to_thread inside if the DAO/API calls are blocking.
        """
        try:
            src = await asyncio.to_thread(self._image_dao.get_image, url)

            if src is None:
                src = await asyncio.to_thread(self._images_api.get_image_src, url)
                await asyncio.to_thread(self._image_dao.add_image, url, src)

        except Exception as e:
            print(e)


    async def fetch_and_cache_item(self, item_id: str):
        try:
            # 1. Fetch item details (blocking request -> thread)
            response = await asyncio.to_thread(self._mashit_api.get_shop_item, item_id)

            listing = response.get("listing", {})
            metadata = listing.get("metadata", {})
            assets = metadata.get("assets", [])

            if not assets:
                return None

            # 2. Prepare async tasks for caching
            tasks = []
            for asset in assets:
                url = self._format_link(asset.get("uri", ""))
                # We call the async function directly here
                tasks.append(self._cache(url))

            # 3. CRITICAL: Execute the tasks and wait for them to finish
            if tasks:
                await asyncio.gather(*tasks)
                print(f"✅ Successfully cached assets for: {listing.get('title')}")

        except Exception as e:
            print(f"❌ Failed to process item {item_id}: {e}")