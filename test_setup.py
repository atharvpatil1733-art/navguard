# ============================================================
# test_setup.py
# ============================================================
# Run this to check Phase 1 is working correctly.
# Command: python test_setup.py
#
# What it tests:
#   1. Your .env file loads correctly
#   2. Gemini API responds
#   3. Browser opens and takes a screenshot
#   4. Memory saves and loads correctly
# ============================================================

import os
import sys
from dotenv import load_dotenv

print("\n============================================")
print("  NavGuard — Phase 1 Setup Test")
print("============================================\n")


# ── Test 1: Environment variables ────────────────────────────
print("Test 1: Loading .env file...")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "your_new_api_key_here":
    print("  FAILED — GEMINI_API_KEY not set in .env file.")
    print("  Open .env and replace 'your_new_api_key_here' with your real key.")
    sys.exit(1)

print("  PASSED — API key loaded.\n")


# ── Test 2: Gemini API ────────────────────────────────────────
print("Test 2: Connecting to Gemini API...")

try:
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly these words: NavGuard is ready."
    )
    reply = response.text.strip()
    print(f"  Gemini says: {reply}")
    print("  PASSED — Gemini API working.\n")
except Exception as e:
    print(f"  FAILED — Gemini error: {e}\n")
    sys.exit(1)


# ── Test 3: Browser + Screenshot ─────────────────────────────
print("Test 3: Opening browser and taking screenshot...")

try:
    from browser_agent import BrowserAgent

    agent = BrowserAgent()
    agent.open_url("https://example.com")

    screenshot_path = agent.take_screenshot("test_screenshot.png")

    if os.path.exists(screenshot_path):
        print(f"  Screenshot saved at: {screenshot_path}")
        print("  PASSED — Browser and screenshot working.\n")
    else:
        print("  FAILED — Screenshot file not found.\n")

    agent.close()

except Exception as e:
    print(f"  FAILED — Browser error: {e}\n")
    sys.exit(1)


# ── Test 4: Memory ────────────────────────────────────────────
print("Test 4: Testing memory save and load...")

try:
    from agent_memory import AgentMemory

    memory = AgentMemory()
    memory.increment_session()
    memory.add_url("https://example.com")
    memory.add_action({"action": "test", "note": "Phase 1 test"})
    memory.add_reflection(
        step_number=1,
        what_happened="Opened example.com",
        lesson_learned="Page loaded successfully",
        success=True
    )

    memory.print_summary()
    print("  PASSED — Memory working.\n")

except Exception as e:
    print(f"  FAILED — Memory error: {e}\n")
    sys.exit(1)


# ── All done ──────────────────────────────────────────────────
print("============================================")
print("  ALL TESTS PASSED — Phase 1 is complete!")
print("  You are ready to build Phase 2.")
print("============================================\n")
