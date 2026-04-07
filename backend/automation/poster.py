from playwright.async_api import async_playwright, expect
import os
import asyncio
from typing import List

# Where we store the logged-in session data so we don't have to login every time
USER_DATA_DIR = os.path.join(os.getcwd(), "fb_session_data")

async def post_to_facebook(media_paths: List[str], caption: str, tags: List[str]):
    """
    Automates the process of posting to Facebook using advanced Playwright handling.
    """
    async with async_playwright() as p:
        # Determine if we are running in a headless server environment
        is_server = os.environ.get("RAILWAY_ENVIRONMENT") is not None or os.environ.get("PORT") is not None
        
        # Using channel="msedge" or "chrome" drastically reduces startup time on Windows by utilizing the pre-installed optimized browser instead of the bundled Chromium binaries.
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            channel="chrome", # Faster cold-start by utilizing installed Chrome
            args=[
                "--disable-notifications", 
                "--start-maximized", 
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ],
            ignore_default_args=["--enable-automation"],
            no_viewport=True
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            print("Navigating to Facebook...")
            # Using networkidle to ensure heavy background scripts download completely
            await page.goto("https://www.facebook.com/", wait_until="networkidle")
            
            # CRITICAL: Allow React client-side hydration to finish. Facebook WILL throw a technical error banner if clicked too early!
            await page.wait_for_timeout(3000)
            
            # Check if we are on the login page (i.e., not logged in)
            email_input = page.locator("input[name='email']")
            if await email_input.is_visible(timeout=3000):
                print("Login required! Please log into your Facebook account in the opened browser window.")
                print("Waiting for you to log in. Proceeding automatically once the feed renders...")
                await page.wait_for_selector('div[role="feed"]', timeout=300000) # Wait up to 5 minutes
                await page.wait_for_timeout(4000) # Wait for login sequence rendering
                print("Login detected. Proceeding...")
            
            print("Clicking Create Post...")
            create_post_locator = page.locator("div[role='button'], span").filter(has_text="What's on your mind").first
            await create_post_locator.wait_for(state="visible", timeout=15000)
            await create_post_locator.click()
            
            # Wait for modal dialog to fully appear safely
            print(f"Uploading {len(media_paths)} Media Files...")
            await page.wait_for_timeout(2000)
            dialog = page.locator("div[role='dialog']").last
            await dialog.wait_for(state="visible")
            
            # Trigger File Upload
            photo_button = dialog.locator('div[aria-label="Add Photo/Video"]').first
            if await photo_button.is_visible(timeout=3000):
                await photo_button.click()
                
            file_input = page.locator("input[type='file'][accept*='image'], input[type='file'][accept*='video'], input[type='file']").first
            # It's an invisible element, so we attach we do wait_for("attached")
            await file_input.wait_for(state="attached", timeout=10000)
            await file_input.set_input_files(media_paths)
            
            print("Entering caption and tracking tags...")
            textbox = dialog.locator("div[role='textbox'][data-lexical-editor='true']").last
            await textbox.wait_for(state="visible")
            
            # Insert the primary caption
            await textbox.fill(caption + "\n\n")
            
            for tag in tags:
                if not tag.startswith('@'):
                    tag = "@" + tag
                    
                # Append the base trigger text sequentially
                await textbox.press_sequentially(tag, delay=35)
                
                # Check for dynamic listbox (dropdown suggestions box)
                listbox = page.locator('ul[role="listbox"]').last
                
                try:
                    # Wait explicitly for the dropdown to attach to DOM and become visible
                    await listbox.wait_for(state="visible", timeout=10000)
                    
                    # Instead of blindly pressing Enter, ensure there's an active option/suggestion populated
                    suggestion_item = listbox.locator('li[role="option"]').first
                    await suggestion_item.wait_for(state="visible", timeout=5000)
                    
                    # Press Enter to finalize active tagging 
                    await page.keyboard.press("Enter")
                except Exception as e:
                    print(f"Fallback: Listbox logic missed for tag {tag}. Reason: {e}")
                    pass
                
                # Space out next tag to reset tagging context
                await textbox.press_sequentially(" ", delay=15)
                    
            print("Clicking Post/Next...")
            await page.wait_for_timeout(1000)
            # Advanced handling of multi-step post (e.g. groups sharing modal flow)
            next_button = dialog.locator('div[role="button"]').filter(has_text="Next").last
            if await next_button.is_visible(timeout=2000):
                await next_button.click()
                await page.wait_for_timeout(1500)
                
            post_button = dialog.locator('div[aria-label="Post"], div[role="button"]').filter(has_text="Post").last
            await post_button.wait_for(state="visible", timeout=5000)
            
            # To actually POST, removing comments or simulating final execute
            await page.wait_for_timeout(1000)
            await post_button.click()
            print("Post submission fired.")
            
            # Await the dialogue closure natively indicating successful dispatch
            await dialog.wait_for(state="hidden", timeout=15000)
            print("Post processed successfully.")
            
            return True, "Success"
            
        except Exception as e:
            print(f"Error during profound automation: {e}")
            return False, str(e)
            
        finally:
            await browser.close()
