# NavGuard 🛡️
### AI Web Navigation Agent — Reflect · Learn · Protect

Built for the **Gemini Live Agent Challenge 2025**

---

## What is NavGuard?

NavGuard is a self-improving AI web navigation agent powered by Gemini that:

- **Navigates** any website autonomously to achieve user goals
- **Reflects** on every action and learns from mistakes in real time
- **Detects dark patterns** — deceptive UI tricks websites use to manipulate users
- **Guides users** through confusing interfaces with adaptive onboarding hints
- **Remembers** lessons across sessions — gets smarter every time it runs

## The Research Contribution

NavGuard introduces a novel **Observe → Decide → Act → Reflect** loop where:

1. The agent observes a page visually using Gemini's vision capabilities
2. Gemini decides the next action based on the goal and past lessons
3. The agent acts on the browser using Playwright
4. Gemini reflects on whether the action worked and saves a lesson to persistent memory
5. On the next run, the agent starts with all previously learned lessons

This creates genuine self-improvement — the agent navigates better on its second visit to a site than its first, because it remembers what worked and what didn't.

## Dark Pattern Detection

NavGuard scans every page for 10 types of manipulative UI design:

- Hidden checkboxes pre-ticked to enroll users in unwanted services
- Fake urgency countdowns and false scarcity warnings
- Confirmshaming — guilt-tripping opt-out buttons
- Misdirection — hiding the real action behind a prominent fake one
- Roach motel patterns — easy to sign up, impossible to cancel
- Hidden costs revealed only at final checkout
- Trick questions with confusing double negatives
- Forced continuity — auto-charging free trials
- Disguised advertisements
- Privacy zuckering

## Architecture
```
User Goal
    ↓
BrowserAgent (Playwright)
    ↓
Gemini Vision — sees screenshot
    ↓
decide_and_reflect() — single combined call
    ├── Action decision
    ├── Dark pattern scan  
    ├── Confusion analysis
    ├── Step reflection
    └── Goal check
    ↓
AgentMemory (JSON persistence)
    ↓
Flask Dashboard (real-time via WebSockets)
```

## Tech Stack

- **Gemini 2.5 Flash** — vision + reasoning + reflection
- **Playwright** — browser automation
- **Flask + SocketIO** — real-time web dashboard
- **Python 3.11**

## Setup
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/navguard
cd navguard

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run locally
python app.py
```

Then open `http://localhost:5000`


## Project Structure
```
navguard/
├── app.py                 # Flask server + WebSocket
├── main.py                # Standalone CLI version
├── browser_agent.py       # Playwright browser control
├── agent_memory.py        # Persistent JSON memory
├── llm_planner.py         # Gemini combined analysis
├── reflect_engine.py      # Self-improvement loop
├── onboarding_lens.py     # Confusion detection
├── dark_pattern_lens.py   # Dark pattern scanner
├── templates/
│   └── index.html         # Live dashboard
├── Dockerfile             # Cloud deployment
├── deploy.sh              # One-command deploy
└── requirements.txt
```


## Author

Built by **Atharv** for the Gemini Live Agent Challenge
