import asyncio
import base64
import os

import httpx

from utils.combiners.helpers.traits_helper import get_traits_info

# 1. Initialize the Semaphore globally to limit concurrency to 2
process_limit = asyncio.Semaphore(2)


def get_mime_type(data: bytes) -> str:
    # ... (Keep your existing get_mime_type code here) ...
    if data.startswith(b'<svg') or data.startswith(b'<?xml'): return "image/svg+xml"
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP': return "image/webp"
    if data.startswith(b'\x89PNG\r\n\x1a\n'): return "image/png"
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'): return "image/gif"
    return "image/png"


class GifService:
    _instance = None

    def __init__(self):
        if GifService._instance is not None:
            raise Exception("This class is a singleton! Use GifService.get_instance()")
        self.process = None
        self.semaphore = asyncio.Semaphore(2)  # Limit concurrency to 2
        self.endpoint = "http://localhost:3000"
        self._is_ready = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        """Spawns the Node.js sidecar process if not already running."""
        if self._is_ready:
            return

        js_path = os.path.join(os.path.dirname(__file__), 'gif.js')

        self.process = await asyncio.create_subprocess_exec(
            'node', js_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for Node to signal that the browser is open
        while True:
            line = await self.process.stdout.readline()
            if b'SERVICE_READY' in line:
                self._is_ready = True
                print("✅ Singleton GifService: Browser process started.")
                break
            if self.process.returncode is not None:
                err = await self.process.stderr.read()
                raise Exception(f"Failed to start Node service: {err.decode()}")

    async def create_gif(self, trait_buffers: list):
        if not self._is_ready:
            await self.start()

        total_ts = await get_traits_info(trait_buffers)
        max_t = max(total_ts)

        async with self.semaphore:
            images = []
            for buf in trait_buffers:
                mime = get_mime_type(buf)
                b64 = base64.b64encode(buf).decode("utf-8")
                images.append(f"data:{mime};base64,{b64}")

            payload = {
                "images": images,
                "max_t": max_t,  # 👈 pass timing info
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    response = await client.post(self.endpoint, json=payload)
                    if response.status_code == 200:
                        return response.content
                    print(f"❌ Service Error: {response.status_code}")
                except Exception as e:
                    print(f"❌ Connection Error: {e}")

            return None