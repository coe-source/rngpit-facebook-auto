from playwright.async_api import async_playwright
import os
import asyncio
from typing import List

# Where we store the logged-in session data so we don't have to login every time
USER_DATA_DIR = os.path.join(os.getcwd(), "fb_session_data")

async def post_to_facebook(media_paths: List[str], caption: str, tags: List[str]):
    """
    Automates the process of posting to Facebook.
    """
    full_caption = caption + "\n\n" + " ".join(tags)
    
    async with async_playwright() as p:
        # Determine if we are running in a headless server environment (like Railway)
        is_server = os.environ.get("RAILWAY_ENVIRONMENT") is not None or os.environ.get("PORT") is not None
        
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True, # Set to True in production
            args=["--disable-notifications", "--start-maximized", "--no-sandbox", "--disable-setuid-sandbox"],
            no_viewport=True
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            print("Navigating to Facebook...")
            await page.goto("https://www.facebook.com/")
            
            # Wait a moment to let the page load
            await page.wait_for_timeout(3000)
            
            # Check if we are on the login page (i.e. not logged in)
            if await page.locator("input[name='email']").is_visible():
                print("Login required! Please log into your Facebook account in the opened browser window.")
                print("Waiting for you to log in. Press enter here when you are done, or simply wait for it to detect navigation.")
                # We can wait for the feed to appear
                await page.wait_for_selector('div[role="feed"]', timeout=300000) # Wait up to 5 minutes for manual login
                print("Login detected. Proceeding...")
            
            # Navigate directly to the user's profile or homepage "Create Post"
            # It's usually easier to click the global "What's on your mind?" input on the homepage
            
            print("Clicking Create Post...")
            create_post_button = page.locator("div[role='button']").filter(has_text="What's on your mind")
            if await create_post_button.count() == 0:
                 # Try another locator
                 create_post_button = page.locator("span").filter(has_text="What's on your mind")
                 
            await create_post_button.first.click()
            await page.wait_for_timeout(2000)
            
            # The dialog opens. Upload the media.
            print(f"Uploading {len(media_paths)} Media Files...")
            
            # Find the photo/video button in the popup dialogue
            photo_button = page.locator('div[aria-label="Add Photo/Video"]')
            # Sometimes it's a generic file input
            file_input = page.locator("input[type='file']").first
            
            if await photo_button.is_visible():
                await photo_button.click()
                await page.wait_for_timeout(1000)
                
            await file_input.set_input_files(media_paths)
            await page.wait_for_timeout(3000)
            
            # The global locator finds 2 elements on Facebook: the feed input and the modal input.
            # We select the last one, which is the active modal popup!
            print("Entering caption and tags...")
            textbox = page.locator("div[role='textbox'][data-lexical-editor='true']").last
            # We use simulated typing to allow Facebook's tagging mechanism to trigger if we type @username
            
            # Let's type the base caption quickly
            await textbox.fill(caption + "\n\n")
            
            # Now, for tags, we need to type them out and potentially press Enter if Facebook suggests them
            # For this MVP, we will paste the pre-formatted @usernames into the textbox.
            # Real dynamic active tagging (selecting from dropdown) is tricky but can be done by typing slowly:
            for tag in tags:
                # Ensure the tag starts with @
                if not tag.startswith('@'):
                    tag = "@" + tag
                    
                # Type the tag WITHOUT a trailing space to trigger the dropdown
                # Slightly slower typing allows the UI to catch up on slower computers
                await textbox.press_sequentially(tag, delay=50)
                
                # CRITICAL: We must wait for Facebook's AJAX request to fetch suggestions
                # and render the dropdown menu before we press Enter!
                # INCREASED wait time to 3500ms to heavily account for slow internet connections
                await page.wait_for_timeout(3500)
                
                # Press Enter to magically select the top profile and turn the text blue
                await page.keyboard.press("Enter")
                
                # Tap space to move the cursor forward for the next person
                await textbox.press_sequentially(" ", delay=20)
                    
            await page.wait_for_timeout(2000)

            print("Clicking Post/Next...")
            # Facebook introduced a multi-step dialog. Check for "Next" button first.
            next_button = page.locator('div[role="button"]').filter(has_text="Next").last
            if await next_button.is_visible():
                await next_button.click()
                await page.wait_for_timeout(2000)

            # Now look for the final Post button
            post_button = page.locator('div[aria-label="Post"]').last
            if await post_button.count() == 0:
                post_button = page.locator('div[role="button"]').filter(has_text="Post").last

            # UNCOMMENT the below line to ACTUALLY post it. 
            # Keeping it commented is safe for first-run tests.
            await post_button.click()
            
            # Wait for it to submit
            await page.wait_for_timeout(5000)
            print("Post submitted successfully.")
            
            return True, "Success"
            
        except Exception as e:
            print(f"Error during automation: {e}")
            return False, str(e)
            
        finally:
            await browser.close()
