import os
import threading
import time
import base64
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
load_dotenv()

from browser_agent import BrowserAgent
from agent_memory import AgentMemory
from llm_planner import decide_and_reflect
from reflect_engine import reflect_on_full_session

app = Flask(__name__)
app.config["SECRET_KEY"] = "navguard_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

agent = None
memory = None
is_running = False
MAX_STEPS = 10

def log(message, type="info"):
    print(message)
    socketio.emit("log", {"message": message, "type": type})

def send_screenshot(path):
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            socketio.emit("screenshot", {"data": data})
    except Exception as e:
        print(f"Screenshot send failed: {e}")

def send_stats(step, dark_count, pages, reflections, task_success):
    socketio.emit("stats", {
        "step": step,
        "dark_patterns": dark_count,
        "pages": pages,
        "reflections": reflections,
        "task_success": task_success
    })

def run_navguard(goal):
    global agent, memory, is_running
    is_running = True
    all_dark_patterns = []
    past_actions = []
    session_reflections = []

    try:
        log(f"Starting NavGuard for goal: {goal}", "info")
        agent = BrowserAgent()
        memory = AgentMemory()
        memory.increment_session()
        agent.open_url("https://duckduckgo.com")
        time.sleep(1)

        for step in range(1, MAX_STEPS + 1):
            if not is_running:
                break

            current_url = agent.get_current_url()
            log(f"── Step {step} ── {current_url[:50]}", "step")
            memory.add_url(current_url)

            # OBSERVE
            log("Observing page...", "info")
            screenshot = agent.take_screenshot(f"step_{step}.png")
            send_screenshot(screenshot)
            elements = agent.get_interactive_elements()
            log(f"Found {len(elements)} interactive elements", "info")
            send_stats(step, len(all_dark_patterns), len(memory.visited_urls), len(session_reflections), memory.stats["tasks_completed"])

            # ONE COMBINED GEMINI CALL
            result = decide_and_reflect(goal, elements, past_actions, memory, screenshot)
            action = result.get("action", "search")

            # Dark patterns
            dark_patterns = result.get("dark_patterns", [])
            all_dark_patterns.extend(dark_patterns)
            if dark_patterns:
                for dp in dark_patterns:
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(dp.get("severity", "medium"), "⚪")
                    log(f"{emoji} DARK PATTERN: {dp.get('type')} — {dp.get('warning')}", "warning")
                socketio.emit("dark_patterns", {"patterns": dark_patterns})
            else:
                log("✓ No dark patterns found", "success")

            # Guidance
            guidance = result.get("guidance", "")
            confusion = result.get("confusion_level", "low")
            if guidance:
                log(f"💡 {guidance}", "hint")

            socketio.emit("confusion", {"level": confusion, "clarity": 5, "guidance": guidance})
            socketio.emit("reflection", {
                "step": step,
                "lesson": result.get("lesson", ""),
                "success": result.get("step_success", False)
            })

            # ACT
            if action == "search":
                query = result.get("query", goal)
                log(f"Searching: {query}", "action")
                agent.search(query)
            elif action == "click":
                index = result.get("index", 0)
                log(f"Clicking index: {index}", "action")
                agent.click_link(index)
            elif action == "open":
                url = result.get("url", "https://duckduckgo.com")
                log(f"Opening: {url}", "action")
                agent.open_url(url)
            elif action == "stop":
                log(f"Stopping: {result.get('stop_reason', '')}", "info")
                break

            time.sleep(3)
            after_screenshot = agent.take_screenshot(f"step_{step}_after.png")
            send_screenshot(after_screenshot)
            memory.add_action(result)
            past_actions.append(result)
            session_reflections.append({
                "step": step,
                "what_happened": f"{action}: {result.get('query') or result.get('url') or result.get('index')}",
                "lesson_learned": result.get("lesson", "")
            })
            send_stats(step, len(all_dark_patterns), len(memory.visited_urls), len(session_reflections), memory.stats["tasks_completed"])

            # CHECK GOAL
            if result.get("goal_achieved"):
                log("🎉 GOAL ACHIEVED!", "success")
                memory.mark_task_completed()
                socketio.emit("goal_achieved", {"url": agent.get_current_url()})
                break

        # END OF SESSION
        log("Running end-of-session reflection...", "reflect")
        reflect_on_full_session(goal, session_reflections, memory)
        log(f"Session complete — {len(session_reflections)} steps, {len(all_dark_patterns)} dark patterns", "info")
        socketio.emit("session_complete", {
            "steps": len(session_reflections),
            "dark_patterns": len(all_dark_patterns),
            "reflections": len(session_reflections)
        })

    except Exception as e:
        log(f"Agent error: {e}", "error")
        socketio.emit("error", {"message": str(e)})

    finally:
        is_running = False
        if agent:
            agent.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/memory")
def get_memory():
    if memory:
        return jsonify({
            "reflections": memory.reflections[-10:],
            "dark_patterns": memory.dark_patterns_found[-10:],
            "confusion_points": memory.confusion_points[-10:],
            "stats": memory.stats,
            "visited_urls": memory.visited_urls[-10:]
        })
    return jsonify({})

@socketio.on("start_agent")
def handle_start(data):
    global is_running
    if is_running:
        emit("log", {"message": "Agent already running!", "type": "warning"})
        return
    goal = data.get("goal", "").strip()
    if not goal:
        emit("log", {"message": "Please enter a goal first.", "type": "error"})
        return
    thread = threading.Thread(target=run_navguard, args=(goal,))
    thread.daemon = True
    thread.start()

@socketio.on("stop_agent")
def handle_stop():
    global is_running
    is_running = False
    log("Agent stopped by user.", "warning")

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    print("\n NavGuard Dashboard starting...")
    print(" Open your browser at: http://localhost:5000\n")
    socketio.run(app, debug=False, port=5000)
