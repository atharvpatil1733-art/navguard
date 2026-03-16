# ============================================================
# browser_agent.py
# ============================================================
# This file controls the browser.
# Think of it as the "hands" of the agent —
# it's what actually clicks, types, and takes screenshots.
# ============================================================

import os
from playwright.sync_api import sync_playwright


class BrowserAgent:

    def __init__(self):
        """
        Start the browser when the agent is created.
        headless=False means you can SEE the browser window.
        Set headless=True if you want it to run invisibly.
        """

        print("[Browser] Starting browser...")

        self.playwright = sync_playwright().start()

        # headless=True for Cloud deployment, False for local testing
        headless = os.environ.get("CLOUD_DEPLOYMENT", "false").lower() == "true"
        self.browser = self.playwright.chromium.launch(headless=headless)

        # Create a browser tab with a realistic screen size
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})

        # Folder where screenshots will be saved
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

        print("[Browser] Ready.")


    def open_url(self, url):
        """
        Open a website.
        Example: agent.open_url("https://google.com")
        """

        print(f"[Browser] Opening: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=15000)


    def take_screenshot(self, filename="screenshot.png"):
        """
        Take a screenshot of the current page.
        Saves the image to the screenshots/ folder.
        Returns the full file path so other modules can use it.

        This is important — Gemini can look at this image
        and understand what the page looks like visually.
        """

        filepath = os.path.join(self.screenshot_dir, filename)
        self.page.screenshot(path=filepath, full_page=False)
        print(f"[Browser] Screenshot saved: {filepath}")
        return filepath


    def search(self, query):
        """
        Find a search box on the current page and type a query.
        Works on DuckDuckGo, Google, Wikipedia, YouTube etc.
        Returns True if search was successful, False if not.
        """

        print(f"[Browser] Searching for: {query}")

        # Try common search box selectors one by one
        selectors = [
            "input[name='q']",          # DuckDuckGo / Google
            "textarea[name='q']",        # Google (newer version)
            "input[type='search']",      # Generic search boxes
            "input[name='search']",      # Some sites use this
            "input#search",              # Some sites use this ID
            "input[type='text']"         # Last resort fallback
        ]

        for selector in selectors:
            box = self.page.query_selector(selector)
            if box:
                print(f"[Browser] Found search box: {selector}")
                box.fill(query)
                box.press("Enter")
                self.page.wait_for_load_state("domcontentloaded")
                return True

        print("[Browser] No search box found on this page.")
        return False


    def click_link(self, index=0):
        """
        Click a link by its position on the page.
        index=0 means the first link, index=1 means the second, etc.
        Returns True if clicked, False if no links found.
        """

        links = self.page.query_selector_all("a")

        if not links:
            print("[Browser] No links found on this page.")
            return False

        # If index is too high, just click the first link
        if index >= len(links):
            print(f"[Browser] Index {index} too high, using 0 instead.")
            index = 0

        print(f"[Browser] Clicking link at index {index}")
        links[index].click()
        self.page.wait_for_load_state("domcontentloaded")
        return True


    def get_current_url(self):
        """
        Return the URL of the page currently open.
        Example return value: "https://google.com/search?q=hello"
        """
        return self.page.url


    def get_page_text(self):
        """
        Get all the visible text on the current page.
        We use this to understand what the page is about.
        Returns a string (could be very long for big pages).
        """

        try:
            text = self.page.inner_text("body")
            # Limit to first 3000 characters to avoid overloading Gemini
            return text[:3000]
        except Exception as e:
            print(f"[Browser] Could not read page text: {e}")
            return ""


    def get_interactive_elements(self):
        """
        Find all clickable/typeable elements on the page.
        Returns a list of text labels for buttons, links, inputs.
        This is what we show Gemini so it knows what it can do.
        """

        elements = []

        try:
            # Get links, buttons, and input fields
            items = self.page.query_selector_all("a, button, input, select")

            for item in items[:30]:  # Max 30 elements to keep it manageable
                try:
                    text = item.inner_text().strip()
                    placeholder = item.get_attribute("placeholder") or ""
                    label = text or placeholder or "(no label)"

                    if len(label) > 1:  # Skip empty elements
                        elements.append(label[:80])  # Trim very long labels

                except Exception:
                    pass  # Skip elements that cause errors

        except Exception as e:
            print(f"[Browser] Error getting elements: {e}")

        return elements


    def close(self):
        """
        Safely close the browser.
        Always call this at the end of your program.
        """

        print("[Browser] Closing browser.")
        self.browser.close()
        self.playwright.stop()
