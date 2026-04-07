import asyncio
import os
import sys

# Add the parent directory to sys.path since python runs from backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from automation.poster import post_to_facebook

async def main():
    media_paths = []
    caption = "Test Caption"
    tags = ["test"]
    print("Testing Playwright Open Browser Feature")
    try:
        success, message = await post_to_facebook(media_paths, caption, tags)
        print(f"Result: {success}, {message}")
    except Exception as e:
        print(f"Failed to post to facebook: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
