import os, base64, json
from google import genai
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def scan_for_dark_patterns(screenshot_path, page_text, elements, url, memory):
    print("[DarkPattern] Scanning page for manipulative patterns...")
    elements_text = "\n".join([f"- {el}" for el in elements[:25]])
    prompt = f"""You are an expert in dark patterns — deceptive UI design.
Scan this page for: hidden_checkbox, fake_urgency, roach_motel, confirmshaming, misdirection, hidden_costs, trick_questions, forced_continuity, disguised_ads, privacy_zuckering.
URL: {url}
ELEMENTS:
{elements_text}
PAGE TEXT: {page_text[:800]}
Look at the screenshot carefully.
Respond ONLY in JSON:
{{"dark_patterns_found":[{{"type":"pattern type","element":"exact element name","description":"how it manipulates users","severity":"low or medium or high","warning_message":"plain English warning for user"}}],"overall_trustworthiness":8,"summary":"one sentence assessment"}}
If no patterns found return: {{"dark_patterns_found":[],"overall_trustworthiness":9,"summary":"No dark patterns detected."}}"""
    try:
        contents = [prompt]
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                contents.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(f.read()).decode()}})
        response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        text = response.text.strip()
        result = json.loads(text[text.find("{"):text.rfind("}")+1])
        patterns = result.get("dark_patterns_found", [])
        trust = result.get("overall_trustworthiness", 10)
        if patterns:
            print(f"[DarkPattern] WARNING: {len(patterns)} pattern(s) found! Trust: {trust}/10")
            for p in patterns:
                memory.add_dark_pattern(url=url, pattern_type=p.get("type","unknown"), description=p.get("description",""), element=p.get("element","unknown"))
                print(f"[DarkPattern] [{p.get('severity','?').upper()}] {p.get('type')}: {p.get('warning_message')}")
        else:
            print(f"[DarkPattern] Clean page. Trust: {trust}/10")
        return patterns
    except Exception as e:
        print(f"[DarkPattern] Scan failed: {e}")
        return []

def format_warnings_for_display(dark_patterns):
    if not dark_patterns:
        return []
    emojis = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    return [f"{emojis.get(p.get('severity','medium'),'⚪')} {p.get('type','').replace('_',' ').title()}: {p.get('warning_message','')} (on: {p.get('element','')})" for p in dark_patterns]

def check_known_patterns(url, memory):
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
    except Exception:
        domain = url
    known = memory.get_dark_patterns_for_url(domain)
    if known:
        print(f"[DarkPattern] Memory: {len(known)} previously recorded patterns for {domain}")
    return known

def generate_protection_advice(dark_patterns, goal):
    if not dark_patterns:
        return None
    summary = "\n".join([f"- {p.get('type')}: {p.get('description')}" for p in dark_patterns])
    prompt = f"""User goal: {goal}
Dark patterns found:
{summary}
Write ONE paragraph of practical advice under 3 sentences to protect this user.
Use "you", be specific, tell exactly what NOT to click."""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[DarkPattern] Advice failed: {e}")
        return "Be cautious — some elements on this page may be designed to mislead you."