import os, base64, json
from google import genai
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def reflect_on_action(goal, action_taken, before_screenshot, after_screenshot, page_text, step_number, memory):
    print(f"\n[Reflect] Reflecting on step {step_number}...")
    prompt = f"""You are a self-improving AI navigation agent performing a reflection.
GOAL: {goal}
STEP: {step_number}
ACTION TAKEN: {action_taken}
PAGE TEXT: {page_text[:800]}
Look at the TWO screenshots (before and after the action).
Respond ONLY in this JSON format:
{{"success": true or false, "progress_made": "one sentence", "lesson": "one sentence", "next_suggestion": "one sentence", "confusion_detected": true or false, "confusion_element": "element name or null", "confusion_reason": "reason or null"}}"""
    try:
        contents = [prompt]
        for path in [before_screenshot, after_screenshot]:
            if path and os.path.exists(path):
                contents.append({"inline_data": {"mime_type": "image/png", "data": image_to_base64(path)}})
        response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        text = response.text.strip()
        result = json.loads(text[text.find("{"):text.rfind("}")+1])
        memory.add_reflection(step_number=step_number, what_happened=action_taken, lesson_learned=result.get("lesson",""), success=result.get("success", False))
        if result.get("confusion_detected") and result.get("confusion_element"):
            memory.add_confusion_point(url="current_page", element=result.get("confusion_element","unknown"), reason=result.get("confusion_reason","unknown"))
        print(f"[Reflect] Step {step_number}: success={result.get('success')} | {result.get('lesson')}")
        return result
    except Exception as e:
        print(f"[Reflect] Failed: {e}")
        return {"success": False, "progress_made": "Unknown", "lesson": "Reflection failed", "next_suggestion": "Try different approach", "confusion_detected": False, "confusion_element": None, "confusion_reason": None}

def reflect_on_full_session(goal, all_reflections, memory):
    print("\n[Reflect] Running end-of-session deep reflection...")
    if not all_reflections:
        return None
    reflection_text = "\n".join([f"Step {r.get('step','?')}: {r.get('what_happened','')} — {r.get('lesson_learned','')}" for r in all_reflections])
    prompt = f"""Analyze this navigation session.
GOAL: {goal}
REFLECTIONS:
{reflection_text}
Respond ONLY in JSON:
{{"biggest_challenge":"one sentence","key_lesson":"one sentence","strategy_improvement":"one sentence","goal_achieved":"yes or no or partial","session_summary":"2-3 sentences"}}"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        result = json.loads(text[text.find("{"):text.rfind("}")+1])
        print(f"[Reflect] Summary: {result.get('session_summary')}")
        memory.add_reflection(step_number=999, what_happened=f"Full session: {goal}", lesson_learned=result.get("key_lesson",""), success=result.get("goal_achieved")=="yes")
        return result
    except Exception as e:
        print(f"[Reflect] Session reflection failed: {e}")
        return None