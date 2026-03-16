import os
import time
import threading
from dotenv import load_dotenv
load_dotenv()

from browser_agent import BrowserAgent
from agent_memory import AgentMemory
from llm_planner import decide_and_reflect
from reflect_engine import reflect_on_full_session

MAX_STEPS = 10
START_URL = "https://duckduckgo.com"

def print_banner():
    print("\n" + "="*50)
    print("   NAVGUARD — AI Web Navigation Agent")
    print("   Reflect · Learn · Protect")
    print("="*50 + "\n")

def print_step_header(step, url):
    print(f"\n{'─'*50}")
    print(f"  STEP {step} of {MAX_STEPS}")
    print(f"  URL: {url[:60]}")
    print(f"{'─'*50}")

def main():
    print_banner()

    agent = BrowserAgent()
    memory = AgentMemory()
    memory.increment_session()

    print("What do you want NavGuard to do?")
    print("Example: find the price of iPhone 16 in India\n")
    goal = input("Your goal: ").strip()

    if not goal:
        print("No goal entered. Exiting.")
        agent.close()
        return

    print(f"\n[NavGuard] Goal: {goal}")
    agent.open_url(START_URL)
    time.sleep(1)

    step = 0
    past_actions = []
    session_reflections = []
    all_dark_patterns = []

    while step < MAX_STEPS:
        step += 1
        current_url = agent.get_current_url()
        print_step_header(step, current_url)
        memory.add_url(current_url)

        # OBSERVE
        print("[NavGuard] Observing page...")
        screenshot = agent.take_screenshot(f"step_{step}.png")
        elements = agent.get_interactive_elements()
        print(f"[NavGuard] Found {len(elements)} interactive elements")

        # ONE COMBINED GEMINI CALL
        result = decide_and_reflect(goal, elements, past_actions, memory, screenshot)
        action = result.get("action", "search")

        # Show dark patterns
        dark_patterns = result.get("dark_patterns", [])
        all_dark_patterns.extend(dark_patterns)
        for dp in dark_patterns:
            emoji = {"high":"🔴","medium":"🟡","low":"🟢"}.get(dp.get("severity","medium"),"⚪")
            print(f"[NavGuard] {emoji} DARK PATTERN: {dp.get('type')} — {dp.get('warning')}")

        # Show guidance
        guidance = result.get("guidance","")
        if guidance:
            print(f"[NavGuard] 💡 {guidance}")

        # ACT
        success = False
        if action == "search":
            query = result.get("query", goal)
            print(f"[NavGuard] Searching: {query}")
            success = agent.search(query)
        elif action == "click":
            index = result.get("index", 0)
            print(f"[NavGuard] Clicking index: {index}")
            success = agent.click_link(index)
        elif action == "open":
            url = result.get("url", START_URL)
            print(f"[NavGuard] Opening: {url}")
            agent.open_url(url)
            success = True
        elif action == "stop":
            print(f"[NavGuard] Stopping: {result.get('stop_reason','')}")
            break

        time.sleep(3)

        memory.add_action(result)
        past_actions.append(result)
        session_reflections.append({
            "step": step,
            "what_happened": f"{action}: {result.get('query') or result.get('url') or result.get('index')}",
            "lesson_learned": result.get("lesson","")
        })

        # CHECK GOAL
        if result.get("goal_achieved"):
            print(f"\n{'='*50}")
            print(f"  GOAL ACHIEVED!")
            print(f"  URL: {agent.get_current_url()}")
            print(f"{'='*50}")
            memory.mark_task_completed()
            break

    # END OF SESSION
    print("\n[NavGuard] Running end-of-session reflection...")
    reflect_on_full_session(goal, session_reflections, memory)

    print(f"\n{'='*50}")
    print("  NAVGUARD SESSION COMPLETE")
    print(f"{'='*50}")
    print(f"  Steps        : {step}")
    print(f"  Dark patterns: {len(all_dark_patterns)}")
    print(f"  Pages visited: {len(memory.visited_urls)}")
    memory.print_summary()

    input("\nPress Enter to close browser...")
    agent.close()

if __name__ == "__main__":
    main()