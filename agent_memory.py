# ============================================================
# agent_memory.py
# ============================================================
# This file is the agent's "brain storage".
# It remembers everything across sessions —
# even if you close the program and open it again tomorrow,
# the agent still remembers what it learned.
#
# Memory is saved to a file called: memory.json
# ============================================================

import json
import os
from datetime import datetime


# The file where memory is saved on disk
MEMORY_FILE = "memory.json"


class AgentMemory:

    def __init__(self):
        """
        Load existing memory from file when agent starts.
        If no memory file exists yet, start fresh.
        """

        print("[Memory] Loading memory...")

        # Try to load memory from the saved file
        if os.path.exists(MEMORY_FILE):
            self._load_from_file()
            print(f"[Memory] Loaded existing memory from {MEMORY_FILE}")
        else:
            # No file yet — start with empty memory
            self._reset()
            print("[Memory] No existing memory found. Starting fresh.")


    def _reset(self):
        """
        Set up empty memory structure.
        Called when no memory file exists yet.
        """

        # List of actions the agent has taken
        self.actions = []

        # List of URLs the agent has visited
        self.visited_urls = []

        # Reflections — what the agent learned after each step
        # Example: {"step": 3, "lesson": "clicking index 0 went to wrong page"}
        self.reflections = []

        # Dark patterns found — per website
        # Example: {"url": "example.com", "pattern": "fake countdown timer"}
        self.dark_patterns_found = []

        # Confusion points — where users/agent got stuck
        # Example: {"url": "example.com", "element": "Subscribe button", "reason": "misleading label"}
        self.confusion_points = []

        # Stats — how many tasks succeeded vs failed
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "dark_patterns_detected": 0,
            "total_sessions": 0
        }


    def _load_from_file(self):
        """
        Read memory from the memory.json file.
        """

        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)

            self.actions          = data.get("actions", [])
            self.visited_urls     = data.get("visited_urls", [])
            self.reflections      = data.get("reflections", [])
            self.dark_patterns_found = data.get("dark_patterns_found", [])
            self.confusion_points = data.get("confusion_points", [])
            self.stats            = data.get("stats", {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "dark_patterns_detected": 0,
                "total_sessions": 0
            })

        except Exception as e:
            print(f"[Memory] Error loading file: {e}. Starting fresh.")
            self._reset()


    def save(self):
        """
        Save all memory to memory.json.
        Call this after every important update
        so nothing is lost if the program crashes.
        """

        data = {
            "actions":              self.actions,
            "visited_urls":         self.visited_urls,
            "reflections":          self.reflections,
            "dark_patterns_found":  self.dark_patterns_found,
            "confusion_points":     self.confusion_points,
            "stats":                self.stats,
            "last_saved":           datetime.now().isoformat()
        }

        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print("[Memory] Saved to memory.json")
        except Exception as e:
            print(f"[Memory] Error saving: {e}")


    # --------------------------------------------------------
    # Methods to ADD things to memory
    # --------------------------------------------------------

    def add_action(self, action):
        """
        Record an action the agent took.
        Example action: {"action": "search", "query": "cheap flights"}
        """
        action["timestamp"] = datetime.now().isoformat()
        self.actions.append(action)
        self.save()


    def add_url(self, url):
        """
        Record a page the agent visited.
        Won't add duplicates.
        """
        if url not in self.visited_urls:
            self.visited_urls.append(url)
            self.save()


    def add_reflection(self, step_number, what_happened, lesson_learned, success):
        """
        Record a reflection — what the agent learned after a step.

        Parameters:
        - step_number: which step this reflection is for (e.g. 3)
        - what_happened: description of the action taken
        - lesson_learned: what the agent thinks it should do differently
        - success: True if the step worked, False if it failed
        """

        reflection = {
            "step": step_number,
            "what_happened": what_happened,
            "lesson_learned": lesson_learned,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        self.reflections.append(reflection)
        self.save()
        print(f"[Memory] Reflection saved for step {step_number}")


    def add_dark_pattern(self, url, pattern_type, description, element):
        """
        Record a dark pattern found on a website.

        Parameters:
        - url: the website where it was found
        - pattern_type: category (e.g. "hidden_checkbox", "fake_urgency")
        - description: what exactly was found
        - element: the UI element that was suspicious
        """

        entry = {
            "url": url,
            "pattern_type": pattern_type,
            "description": description,
            "element": element,
            "timestamp": datetime.now().isoformat()
        }

        self.dark_patterns_found.append(entry)
        self.stats["dark_patterns_detected"] += 1
        self.save()
        print(f"[Memory] Dark pattern recorded: {pattern_type} on {url}")


    def add_confusion_point(self, url, element, reason):
        """
        Record a moment where the agent or user got confused.

        Parameters:
        - url: page where confusion happened
        - element: what element caused confusion
        - reason: why it was confusing
        """

        entry = {
            "url": url,
            "element": element,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        self.confusion_points.append(entry)
        self.save()
        print(f"[Memory] Confusion point recorded on {url}")


    def mark_task_completed(self):
        """ Call this when a task succeeds. """
        self.stats["tasks_completed"] += 1
        self.save()


    def mark_task_failed(self):
        """ Call this when a task fails. """
        self.stats["tasks_failed"] += 1
        self.save()


    def increment_session(self):
        """ Call this at the start of every new run. """
        self.stats["total_sessions"] += 1
        self.save()


    # --------------------------------------------------------
    # Methods to READ from memory
    # --------------------------------------------------------

    def get_recent_reflections(self, count=5):
        """
        Get the most recent N reflections.
        Used to feed context back to Gemini.
        """
        return self.reflections[-count:]


    def get_recent_actions(self, count=10):
        """
        Get the most recent N actions.
        """
        return self.actions[-count:]


    def get_dark_patterns_for_url(self, url):
        """
        Get all dark patterns previously found on a specific URL.
        Useful so the agent already knows what to watch for
        on sites it has visited before.
        """
        return [p for p in self.dark_patterns_found if p["url"] == url]


    def last_action(self):
        """
        Return the most recent action taken.
        Returns None if no actions yet.
        """
        if not self.actions:
            return None
        return self.actions[-1]


    def print_summary(self):
        """
        Print a human-readable summary of everything in memory.
        Useful for debugging and demos.
        """

        print("\n========== NAVGUARD MEMORY SUMMARY ==========")
        print(f"  Total sessions      : {self.stats['total_sessions']}")
        print(f"  Tasks completed     : {self.stats['tasks_completed']}")
        print(f"  Tasks failed        : {self.stats['tasks_failed']}")
        print(f"  Dark patterns found : {self.stats['dark_patterns_detected']}")
        print(f"  Pages visited       : {len(self.visited_urls)}")
        print(f"  Total reflections   : {len(self.reflections)}")

        if self.dark_patterns_found:
            print("\n  Recent dark patterns:")
            for dp in self.dark_patterns_found[-3:]:
                print(f"    - [{dp['pattern_type']}] on {dp['url']}")

        if self.reflections:
            print("\n  Last reflection:")
            last = self.reflections[-1]
            print(f"    Step {last['step']}: {last['lesson_learned']}")

        print("==============================================\n")
