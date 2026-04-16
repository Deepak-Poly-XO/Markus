import anthropic
import json
import re
import os
from config import API_KEY, MARKUS_PERSONA
from memory import get_memory_context, save_conversation_summary, add_fact
from self_evolve import evolve_and_execute
from spotify_control import (play_song, pause, resume, skip,previous, set_volume as spotify_volume, what_is_playing, play_playlist)
from vision import see_screen, click_on, help_with_error, read_screen_text

RESPONSE_MODEL = "claude-sonnet-4-6"
INTENT_MODEL   = "claude-haiku-4-5-20251001"
FACT_MODEL     = "claude-haiku-4-5-20251001"


client = anthropic.Anthropic(api_key=API_KEY)
conversation_history = []

# ── INTENT CLASSIFIER ──────────────────────────────────
INTENT_SYSTEM = """
Classify user message. Return ONLY JSON:
{"type":"action|question|memory|conversation|vision|file_read|spotify","needs_code":bool,"needs_web":bool,"spotify":bool,"task":"brief task"}

Types:
action       → do something on PC (needs_code=true if requires Python)
question     → needs info (needs_web=true if real-time)
memory       → save/delete/recall something
conversation → casual chat
vision       → look at screen, click, describe screen
file_read    → read/explain a file
spotify      → music control (spotify=true)

Return ONLY raw JSON.
"""

def classify_intent(user_input):
    try:
        response = client.messages.create(
            model=INTENT_MODEL,
            max_tokens=100,
            system=INTENT_SYSTEM,
            messages=[{"role": "user", "content": user_input}]
        )
        raw  = response.content[0].text.strip()
        raw  = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except:
        return {"type": "conversation", "needs_code": False,
                "needs_web": False, "task": user_input}

# ── FACT EXTRACTION ────────────────────────────────────
FACT_SYSTEM = """
Detect save or delete memory intent. Return ONLY JSON.

{"action": "save", "key": "keyword", "value": "rocket"}
{"action": "delete", "key": "keyword"}
{"action": "save_conversation"}
{"action": "none"}

Return ONLY raw JSON.
"""

def extract_and_save_facts(user_input):
    try:
        response = client.messages.create(
            model=FACT_MODEL,
            max_tokens=50,
            system=FACT_SYSTEM,
            messages=[{"role": "user", "content": user_input}]
        )
        raw  = response.content[0].text.strip()
        data = json.loads(raw)
        action = data.get("action")

        if action == "save":
            add_fact(data["key"], data["value"])
            print(f"🧠 Saved: {data['key']} = {data['value']}")
        elif action == "save_conversation":
            summarize_and_save()
        elif action == "delete":
            from memory import remove_fact
            removed, key = remove_fact(data["key"])
            print(f"🧠 {'Removed' if removed else 'Not found'}: {key}")
    except:
        pass

# ── WEB SEARCH ─────────────────────────────────────────
def web_answer(task):
    from search import search_web
    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=30,
            system="Convert to a short precise Google search query. Return ONLY the query.",
            messages=[{"role": "user", "content": task}]
        )
        query = response.content[0].text.strip()
        print(f"🔍 Searching: {query}")
        results = search_web(query)

        # If results seem vague — try fetching first result directly
        if results and len(results) < 200:
            import requests
            from ddgs import DDGS
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=1))
                if hits and hits[0].get("href"):
                    try:
                        page = requests.get(hits[0]["href"], timeout=5)
                        # Extract just text content
                        import re
                        text = re.sub(r'<[^>]+>', ' ', page.text)
                        text = re.sub(r'\s+', ' ', text)[:2000]
                        return text
                    except:
                        pass
        return results
    except:
        return ""
    
# Spotify control
def handle_spotify(task):
    task_lower = task.lower()

    if "pause"    in task_lower: return pause()
    if "resume"   in task_lower: return resume()
    if "skip"     in task_lower: return skip()
    if "previous" in task_lower: return previous()
    if "next"     in task_lower: return skip()
    if "what"     in task_lower and "playing" in task_lower:
        return what_is_playing()
    if "volume"   in task_lower:
        # Extract number
        import re
        nums = re.findall(r'\d+', task_lower)
        if nums:
            return spotify_volume(nums[0])

    # Check if playlist
    if "playlist" in task_lower:
        query = task_lower.replace("play playlist", "").replace(
                "play", "").replace("playlist", "").strip()
        return play_playlist(query)

    # Default — play song
    query = task_lower.replace("play", "").replace(
            "on spotify", "").replace("spotify", "").strip()
    return play_song(query)

# ── MAIN THINK ─────────────────────────────────────────
def think(user_input):
    try:
        original_input = user_input
        extract_and_save_facts(original_input)

        intent     = classify_intent(original_input)
        print(f"🧠 Intent: {intent}")

        itype      = intent.get("type")
        needs_code = intent.get("needs_code", False)
        needs_web  = intent.get("needs_web", False)
        task       = intent.get("task", original_input)

        if itype == "file_read":
            print("📂 Reading file...")
            import re

            # Extract filename from task
            file_match = re.findall(r'[\w]+\.\w+', task)
            if not file_match:
                return get_claude_response("I couldn't find a filename in your request sir.")

            filename  = file_match[0]
            markus_dir = os.path.dirname(os.path.abspath(__file__))
            file_path  = os.path.join(markus_dir, filename)

            if not os.path.exists(file_path):
                # Try searching common locations
                home = os.path.expanduser("~")
                for root, dirs, files in os.walk(markus_dir):
                    for f in files:
                        if f.lower() == filename.lower():
                            file_path = os.path.join(root, f)
                            break

            if not os.path.exists(file_path):
                return get_claude_response(
                    f"I couldn't find {filename} sir. Make sure the filename is correct."
                )

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                print(f"📂 Read {filename} — {len(content)} chars")

                return get_claude_response(
                    f"User asked: {original_input}\n\n"
                    f"File: {filename}\n"
                    f"Content:\n{content}\n\n"
                    f"Explain this file naturally and concisely as MARKUS speaking out loud. "
                    f"No markdown. Focus on what it does, not line by line."
                )

            except Exception as e:
                return get_claude_response(f"I couldn't read {filename}: {e}")

        if itype == "vision":
            print("👁️ Vision activated...")
            task_lower = task.lower()

            # ── If needs code AND vision — see screen then evolve ──
            if intent.get("needs_code"):
                print("👁️ + 🧬 Vision + Evolve...")
                screen_context = see_screen(
                    f"Describe exactly what you see — file paths, folder names, "
                    f"current directory, any relevant details for this task: {original_input}"
                )
                print(f"👁️ Screen context: {screen_context}")

                # Pass screen context to self evolve
                enriched_task = f"{original_input}. Context from screen: {screen_context}"
                result = evolve_and_execute(enriched_task)
                return get_claude_response(
                    f"You analyzed the screen and executed: {result}. "
                    f"Confirm naturally."
                )

            # ── Vision only — just describe/analyze ──
            elif "error" in task_lower or "fix" in task_lower:
                result = help_with_error()
            elif "click" in task_lower:
                what   = task_lower.replace("click on","").replace("click","").strip()
                result = click_on(what)
            elif "read" in task_lower or "text" in task_lower:
                result = read_screen_text()
            else:
                result = see_screen(original_input)

            return get_claude_response(
                f"Screen analysis: {result}. Respond naturally as MARKUS."
            )

        # ── ACTION ──
        if needs_code:
            print(f"🧬 Auto-evolving: {task}")
            result = evolve_and_execute(task)
            return get_claude_response(
                f"You just executed: '{task}'. Result: {result}. "
                f"Confirm naturally."
            )
        
        if intent.get("spotify"):
            result = handle_spotify(task)
            return get_claude_response(
                f"Spotify result: {result}. Confirm naturally."
            )

        # ── WEATHER — dedicated API ──
        weather_keywords = ["weather", "temperature", "forecast",
                           "snow", "rain", "cold", "warm", "hot"]
        if any(w in original_input.lower() for w in weather_keywords):
            from weather import get_weather
            # Extract city from task
            city_response = client.messages.create(
                model=INTENT_MODEL,
                max_tokens=10,
                system="Extract ONLY the city name. Return just the city. If none mentioned return Calgary.",
                messages=[{"role": "user", "content": original_input}]
            )
            city = city_response.content[0].text.strip()
            print(f"🌤️  Fetching weather for: {city}")
            weather_data = get_weather(city)
            if weather_data:
                user_input = f"""
User asked: {original_input}
Real weather data: {weather_data}
Answer naturally as MARKUS. Give specific numbers.
"""
                return get_claude_response(user_input)

        # ── WEB SEARCH ──
        if needs_web:
            context = web_answer(task)
            if context:
                user_input = f"""
User asked: {original_input}
Real time data: {context}
Answer naturally as MARKUS. Be direct with specific numbers if available.
"""

        return get_claude_response(user_input)

    except Exception as e:
        print(f"❌ Brain error: {e}")
        return "I ran into an issue Deepu. Check the terminal."

def get_claude_response(user_input):
    memory_context = get_memory_context()
    full_system    = MARKUS_PERSONA + f"\n\nWhat you know:\n{memory_context}"

    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    response = client.messages.create(
        model=RESPONSE_MODEL,
        max_tokens=1024,
        system=full_system,
        messages=conversation_history
    )

    reply = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    if len(conversation_history) % 6 == 0:
        summarize_and_save()

    return reply

def summarize_and_save():
    try:
        if len(conversation_history) < 2:
            return
        valid = [m for m in conversation_history
                 if isinstance(m.get("content"), str)
                 and len(m["content"].strip()) > 5]
        if len(valid) < 2:
            return
        recent = valid[-6:]
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=60,
            system="Summarize in ONE plain sentence. No markdown. No dashes.",
            messages=recent
        )
        summary = re.sub(r'[\*\#\`\-]+', '',
                  response.content[0].text.strip()).strip()
        if summary:
            save_conversation_summary(summary)
            print(f"🧠 Saved: {summary}")
    except Exception as e:
        print(f"🧠 Save error: {e}")