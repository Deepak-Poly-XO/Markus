import anthropic
from config import API_KEY, MARKUS_PERSONA
import json
from controller import execute_command, open_and_write
from memory import get_memory_context, save_conversation_summary, add_fact, remove_fact, clear_all_memory, clear_conversations

client = anthropic.Anthropic(api_key=API_KEY)
conversation_history = []

from search import search_web

COMMAND_SYSTEM = """
You are a command parser for MARKUS AI.
The input may have missing words due to speech recognition.

IMPORTANT: If the message mentions an app name AND writing/explaining/describing,
always use open_and_write even if "open" word is missing.

Common mishearings:
"know that" / "no pad" / "node" / "not pad" → notepad
"sport if i" / "spotif"                      → spotify

Valid actions:
- open_app       → target: app name
- close_app      → target: app name  
- open_website   → target: site name
- volume         → target: up/down/mute/unmute
- system_stats   → target: ""
- screenshot     → target: ""
- open_and_write → target: "appname|text"
- none           → target: ""

Examples:
"Notepad and explain machine learning"     → {"action": "open_and_write", "target": "notepad|Machine learning is a subset of AI that enables computers to learn from data without being explicitly programmed."}
"Open notepad write about AI"              → {"action": "open_and_write", "target": "notepad|Artificial Intelligence is the simulation of human intelligence by machines."}
"know that and explain quantum computing"  → {"action": "open_and_write", "target": "notepad|Quantum computing uses quantum mechanical phenomena to perform calculations exponentially faster than classical computers."}

Return ONLY JSON. No explanation. No markdown.
"""

FACT_SYSTEM = """
Analyze the user's message. Detect save, delete, or conversation save intent.

Save fact examples:
"the keyword is bull"        → {"action": "save", "key": "keyword", "value": "bull"}
"remember my code ABC123"    → {"action": "save", "key": "code", "value": "ABC123"}

Save conversation examples:
"save this conversation"     → {"action": "save_conversation"}
"remember this chat"         → {"action": "save_conversation"}
"log this session"           → {"action": "save_conversation"}

Delete examples:
"forget the keyword"         → {"action": "delete", "key": "keyword"}
"clear your memory"          → {"action": "clear_all"}
"forget our conversations"   → {"action": "clear_conversations"}

Nothing to save/delete:
"what is the weather"        → {"action": "none"}

Return ONLY raw JSON. No markdown. No explanation.
"""

def extract_and_save_facts(user_input):
    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=50,
            system=FACT_SYSTEM,
            messages=[{"role": "user", "content": user_input}]
        )
        import json
        raw  = response.content[0].text.strip()
        data = json.loads(raw)
        action = data.get("action")

        if action == "save":
            add_fact(data["key"], data["value"])
            print(f"🧠 Saved: {data['key']} = {data['value']}")

        elif action == "save_conversation":
            summarize_and_save()
            print("🧠 Conversation saved on request")

        elif action == "delete":
            removed, matched_key = remove_fact(data["key"])
            if removed:
                print(f"🧠 Removed: {matched_key}")
            else:
                print(f"🧠 Not found: {data['key']}")

        elif action == "clear_all":
            clear_all_memory()

        elif action == "clear_conversations":
            clear_conversations()

    except:
        pass

def parse_command(user_input):
    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=60,
            system=COMMAND_SYSTEM,
            messages=[{"role": "user", "content": user_input}]
            # ← NO conversation_history here, fresh every time
        )
        raw  = response.content[0].text.strip()
        # Strip any markdown code blocks
        raw  = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except:
        return {"action": "none", "target": ""}

def extract_city(user_input):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=20,
        system="Extract ONLY the city name from the user's message. Return just the city name, nothing else. If no city mentioned return 'Calgary'.",
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text.strip()

def build_search_query(user_input):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=50,
        system="Convert the user's question into a short, precise Google search query. Return ONLY the search query, nothing else.",
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text.strip()

def detect_write_command(user_input):
    """Directly detect write commands without relying on JSON parser"""
    text  = user_input.lower()
    

    cancel_words = ["close", "shut", "exit", "kill", "stop", "cancel"]
    if any(w in text for w in cancel_words):
        return None
    # App names to check
    apps  = ["notepad", "know that", "no pad", "node pad"]
    write_words = ["write", "explain", "describe", "type", "note"]

    app_found   = next((a for a in apps if a in text), None)
    write_found = any(w in text for w in write_words)

    if not app_found or not write_found:
        return None

    # Extract what to write — ask Claude
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=150,
        system="Extract what the user wants written. Return ONLY the text to write, nothing else. No quotes. No explanation. If they said 'write something' or 'write whatever', write a short thoughtful sentence of your own.",
        messages=[{"role": "user", "content": user_input}]
    )
    write_text = response.content[0].text.strip()

    return {
        "action": "open_and_write",
        "app": "notepad",
        "text": write_text
    }

def think(user_input):
    try:
        original_input = user_input
        # ── STEP 1: Save facts ──
        extract_and_save_facts(original_input)

        garbage_signals = [
        "def ", "import ", "return ", "class ",
        "client.", "logger.", "print(", "🧠", "🤖"
        ]
        if any(g in user_input for g in garbage_signals):
            print("⚠️  Garbage transcription detected, ignoring.")
            return None 

        write_cmd = detect_write_command(original_input)
        if write_cmd:
            print(f"✍️  Write command: {write_cmd['text'][:40]}...")
            result = open_and_write(write_cmd["app"], write_cmd["text"])
            return get_claude_response(
                f"You just opened notepad and wrote: '{write_cmd['text']}'. Confirm naturally."
            )
        

        # ── STEP 2: PC Command ──
        command = parse_command(original_input)
        print(f"🖥️  Command detected: {command}")

        if command["action"] != "none":
            result = execute_command(command)
            if result:
                user_input = f"You just executed: {result}. Confirm naturally as MARKUS."
            return get_claude_response(user_input)  # ← exit early, skip weather/search

        live_keywords = [
            "news", "today", "currently",
            "latest", "war", "score", "stock", "price",
            "who won", "what happened", "search"
        ]

        weather_keywords = ["weather", "temperature", "snow",
                           "rain", "forecast", "cold", "warm",
                           "outside", "walk", "hot"]
        context = ""

        # ── STEP 3: Weather ──
        if any(w in original_input.lower() for w in weather_keywords):
            from weather import get_weather
            city = extract_city(original_input)
            print(f"🌤️  Fetching weather for: {city}")
            weather_data = get_weather(city)
            if weather_data:
                context = weather_data

        # ── STEP 4: Web search ──
        elif any(w in original_input.lower() for w in live_keywords):
            search_query = build_search_query(original_input)
            print(f"🔍 Searching: {search_query}")
            context = search_web(search_query)

        if context:
            user_input = f"""
User asked: {original_input}
Real data: {context}
Answer naturally as MARKUS. Be direct and concise.
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
        model="claude-opus-4-5",
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
        # Need at least one exchange
        if len(conversation_history) < 2:
            return

        # Filter only valid non-empty messages
        valid = [
            m for m in conversation_history
            if isinstance(m.get("content"), str) 
            and len(m["content"].strip()) > 5
        ]

        if len(valid) < 2:
            return

        recent = valid[-6:]

        summary_response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=60,
            system="Summarize in ONE plain sentence. No markdown. No dashes. No bold.",
            messages=recent
        )

        summary = summary_response.content[0].text.strip()
        import re
        summary = re.sub(r'[\*\#\`\-]+', '', summary).strip()

        if summary:
            save_conversation_summary(summary)
            print(f"🧠 Saved: {summary}")

    except Exception as e:
        print(f"🧠 Save error: {e}")