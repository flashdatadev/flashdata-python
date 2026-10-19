"""One paid realtime request with native async HTTP."""

import asyncio
from flashdata import AsyncFlashData


async def main():
    async with AsyncFlashData() as client:
        print(await client.youtube.transcript("dQw4w9WgXcQ", language="en", auto=True))


if __name__ == "__main__":
    asyncio.run(main())
