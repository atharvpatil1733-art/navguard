import os, base64, json
from google import genai
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_page_for_confusion(screenshot_path, page_text, elements, goal, memory):
    print("[Onboarding] Analyzing page for confusion signals...")
    elements_text = "\n".join([f"- {el}" for el in elements[:20]])
    prompt = f"""You are a UX researcher. Analyze this page for confusion.
GOAL: {goal}
ELEMENTS:
{elements_text}
PAGE TEXT: {page_text[:600]}
Look at the screenshot and rate confusion level.
Respond ONLY in JSON:
{{"confusion_level":"low or medium or high","is_goal_path_clear":true or false,"confusing_elements":[],"clarity_score":5,"main_issue":"one sentence or null","guidance_for_user":"one sentence telling exactly what to do","improvement_suggestion":"one sentence"}}"""
    try:
        contents = [prompt]
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                contents.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(f.read()).decode()}})
        response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        text = response.text.strip()
        result = json.loads(text[text.find("{"):text.rfind("}")+1])
        print(f"[Onboarding] Confusion: {result.get('confusion_level')} | Clarity: {result.get('clarity_score')}/10")
        if result.get("confusion_level") in ["medium", "high"]:
            memory.add_confusion_point(url="current_page", element=", ".join(result.get("confusing_elements", ["unknown"])), reason=result.get("main_issue", "unclear UI"))
        print(f"[Onboarding] Guidance: {result.get('guidance_for_user')}")
        return result
    except Exception as e:
        print(f"[Onboarding] Failed: {e}")
        return {"confusion_level": "low", "is_goal_path_clear": True, "confusing_elements": [], "clarity_score": 5, "main_issue": None, "guidance_for_user": "Proceed with the most relevant option.", "improvement_suggestion": None}

def detect_repeated_failure(actions_history, threshold=2):
    if len(actions_history) < threshold:
        return False
    recent = [a.get("action") for a in actions_history[-threshold:]]
    if len(set(recent)) == 1:
        print(f"[Onboarding] WARNING: Repeated action detected — possible stuck loop")
        return True
    return False

def generate_adaptive_hint(goal, confusion_analysis, past_failures, memory):
    print("[Onboarding] Generating adaptive hint...")
    lessons = "\n".join([f"- {r.get('lesson_learned','')}" for r in memory.get_recent_reflections(3)])
    prompt = f"""Agent is stuck trying to: {goal}
Confusion: {confusion_analysis.get('main_issue', 'none')}
Recent lessons: {lessons if lessons else 'none'}
Past failures: {past_failures}
Give ONE specific actionable hint in one sentence. No JSON, just the hint."""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        hint = response.text.strip()
        print(f"[Onboarding] Hint: {hint}")
        return hint
    except Exception as e:
        print(f"[Onboarding] Hint failed: {e}")
        return "Try using the search bar to find what you need."