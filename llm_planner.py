import os, base64, json, time
from google import genai
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def call_gemini_with_retry(contents, retries=3):
    """
    Call Gemini with automatic retry if rate limited.
    Waits the exact time Gemini tells us to wait.
    """
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents
            )
            return response
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Extract wait time from error message
                wait = 15
                try:
                    import re
                    match = re.search(r'retryDelay.*?(\d+)s', error_str)
                    if match:
                        wait = int(match.group(1)) + 2
                except:
                    pass
                print(f"[Gemini] Rate limited. Waiting {wait}s before retry {attempt+1}/{retries}...")
                time.sleep(wait)
            else:
                print(f"[Gemini] Error: {e}")
                return None
    return None

def decide_and_reflect(goal, elements, past_actions, memory, screenshot_path=None):
    """
    ONE single Gemini call that does everything:
    - Decides next action
    - Scans for dark patterns
    - Checks confusion level
    - Reflects on last action
    - Checks if goal achieved

    This replaces 5 separate calls with 1.
    Saves 80% of API quota.
    """
    print("[NavGuard] Calling Gemini (combined analysis)...")

    lessons = "\n".join([
        f"- Step {r.get('step','?')}: {r.get('lesson_learned','')}"
        for r in memory.get_recent_reflections(3)
    ])

    elements_text = "\n".join([
        f"{i}: {el}" for i, el in enumerate(elements[:15])
    ])

    past_text = "\n".join([f"- {a}" for a in past_actions[-3:]])

    prompt = f"""You are NavGuard — a self-improving AI web navigation agent.
Analyze the current page screenshot and answer ALL of the following in ONE response.

GOAL: {goal}

INTERACTIVE ELEMENTS (index: label):
{elements_text}

PAST ACTIONS:
{past_text if past_text else "None yet"}

LESSONS FROM MEMORY:
{lessons if lessons else "None yet — first step"}

Look at the screenshot carefully and respond ONLY in this exact JSON format:

{{
  "action": "search or click or open or stop",
  "query": "search query if action is search, else null",
  "index": 0,
  "url": "full url if action is open, else null",
  "stop_reason": "reason if action is stop, else null",

  "goal_achieved": true or false,
  "goal_reason": "one sentence — why goal is or isn't achieved",

  "lesson": "one sentence — what to remember from the last action",
  "step_success": true or false,

  "confusion_level": "low or medium or high",
  "guidance": "one sentence — exactly what to do next",

  "dark_patterns": [
    {{
      "type": "pattern type",
      "element": "element name",
      "severity": "low or medium or high",
      "warning": "plain English warning"
    }}
  ]
}}

RULES FOR ACTION:
- If past actions show the same search repeated 2+ times, use "open" to go directly to the site instead
- Never repeat a failed action
- If dark patterns exist, avoid those elements
- Use "stop" only when goal is fully achieved or truly impossible
- Dark patterns list can be empty [] if none found"""

    try:
        contents = [prompt]
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            contents.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_data
                }
            })
            print("[NavGuard] Screenshot included in analysis...")

        response = call_gemini_with_retry(contents)
        if not response:
            raise Exception("All retries failed")

        text = response.text.strip()
        result = json.loads(text[text.find("{"):text.rfind("}")+1])

        # Save lesson to memory immediately
        if result.get("lesson"):
            memory.add_reflection(
                step_number=len(past_actions)+1,
                what_happened=str(past_actions[-1]) if past_actions else "first step",
                lesson_learned=result.get("lesson",""),
                success=result.get("step_success", False)
            )
            print(f"[NavGuard] Lesson saved: {result.get('lesson')}")

        # Save dark patterns to memory
        for dp in result.get("dark_patterns", []):
            memory.add_dark_pattern(
                url="current_page",
                pattern_type=dp.get("type","unknown"),
                description=dp.get("warning",""),
                element=dp.get("element","unknown")
            )

        # Save confusion if medium or high
        if result.get("confusion_level") in ["medium","high"]:
            memory.add_confusion_point(
                url="current_page",
                element="page",
                reason=result.get("guidance","")
            )

        print(f"[NavGuard] Action: {result.get('action','?').upper()}")
        print(f"[NavGuard] Confusion: {result.get('confusion_level')} | Goal achieved: {result.get('goal_achieved')}")
        if result.get("dark_patterns"):
            print(f"[NavGuard] Dark patterns: {len(result.get('dark_patterns'))} found")

        return result

    except Exception as e:
        print(f"[NavGuard] Combined call failed: {e}")
        # Smart fallback — if we've searched before, go directly to site
        if past_actions and all(a.get("action") == "search" for a in past_actions[-2:]):
            return {
                "action": "open",
                "url": "https://www.flipkart.com",
                "query": None, "index": 0, "stop_reason": None,
                "goal_achieved": False, "goal_reason": "Navigating directly",
                "lesson": "Direct navigation works better when search loops",
                "step_success": False,
                "confusion_level": "low", "guidance": "Navigate directly to target site",
                "dark_patterns": []
            }
        return {
            "action": "search", "query": goal,
            "index": 0, "url": None, "stop_reason": None,
            "goal_achieved": False, "goal_reason": "Fallback search",
            "lesson": "API unavailable — retrying",
            "step_success": False,
            "confusion_level": "low", "guidance": "Try again",
            "dark_patterns": []
        }

def check_goal_achieved(goal, page_text, screenshot_path, memory):
    """Lightweight goal check — no extra Gemini call needed,
    result already comes from decide_and_reflect."""
    return False  # handled inside decide_and_reflect now