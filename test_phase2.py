import os
from dotenv import load_dotenv
load_dotenv()

print("\n============================================")
print("  NavGuard — Phase 2 Test")
print("============================================\n")

from agent_memory import AgentMemory
from browser_agent import BrowserAgent

memory = AgentMemory()
agent = BrowserAgent()

print("Test 1: Dark pattern scanner...")
try:
    from dark_pattern_lens import scan_for_dark_patterns, format_warnings_for_display
    agent.open_url("https://www.amazon.in")
    screenshot = agent.take_screenshot("test_dark.png")
    page_text = agent.get_page_text()
    elements = agent.get_interactive_elements()
    patterns = scan_for_dark_patterns(screenshot, page_text, elements, agent.get_current_url(), memory)
    warnings = format_warnings_for_display(patterns)
    print(f"  Patterns found: {len(patterns)}")
    for w in warnings:
        print(f"  {w}")
    print("  PASSED\n")
except Exception as e:
    print(f"  FAILED: {e}\n")

print("Test 2: Onboarding confusion detector...")
try:
    from onboarding_lens import analyze_page_for_confusion
    screenshot = agent.take_screenshot("test_onboarding.png")
    analysis = analyze_page_for_confusion(screenshot, agent.get_page_text(), agent.get_interactive_elements(), "find and buy a laptop", memory)
    print(f"  Confusion: {analysis.get('confusion_level')} | Clarity: {analysis.get('clarity_score')}/10")
    print(f"  Guidance: {analysis.get('guidance_for_user')}")
    print("  PASSED\n")
except Exception as e:
    print(f"  FAILED: {e}\n")

print("Test 3: Reflect engine...")
try:
    from reflect_engine import reflect_on_action
    before = agent.take_screenshot("before.png")
    agent.search("laptop under 50000")
    after = agent.take_screenshot("after.png")
    reflection = reflect_on_action("find laptop under 50000", "searched for laptop", before, after, agent.get_page_text(), 1, memory)
    print(f"  Success: {reflection.get('success')} | Lesson: {reflection.get('lesson')}")
    print("  PASSED\n")
except Exception as e:
    print(f"  FAILED: {e}\n")

print("Test 4: Vision planner...")
try:
    from llm_planner import decide_next_action
    screenshot = agent.take_screenshot("planner.png")
    decision = decide_next_action("find laptop under 50000", agent.get_interactive_elements(), [], memory, screenshot)
    print(f"  Decision: {decision}")
    print("  PASSED\n")
except Exception as e:
    print(f"  FAILED: {e}\n")

agent.close()
memory.print_summary()
print("============================================")
print("  Phase 2 test complete!")
print("============================================\n")

