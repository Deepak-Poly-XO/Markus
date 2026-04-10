import anthropic
from config import API_KEY, MARKUS_PERSONA
import json
from controller import execute_command

client = anthropic.Anthropic(api_key=API_KEY)
conversation_history = []

from search import search_web

COMMAND_SYSTEM = """
You are a command parser for MARKUS AI.
Analyze the user's message and return ONLY a JSON object.

Valid actions:
- open_app      → target: app name
- close_app     → target: app name  
- open_website  → target: site name or URL
- volume        → target: up / down / mute / unmute
- system_stats  → target: ""
- screenshot    → target: ""
- none          → target: "" (normal conversation)

Examples:
"Open Spotify"           → {"action": "open_app", "target": "spotify"}
"Close Chrome"           → {"action": "close_app", "target": "chrome"}
"Go to YouTube"          → {"action": "open_website", "target": "youtube"}
"Turn up the volume"     → {"action": "volume", "target": "up"}
"What's my battery?"     → {"action": "system_stats", "target": ""}
"Take a screenshot"      → {"action": "screenshot", "target": ""}
"What's the weather?"    → {"action": "none", "target": ""}

Return ONLY the JSON. No explanation. No markdown.
"""

def parse_command(user_input):
    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=50,
            system=COMMAND_SYSTEM,
            messages=[{"role": "user", "content": user_input}]
        )
        raw  = response.content[0].text.strip()
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

def think(user_input):
    try:

        command = parse_command(user_input)
        print(f"🖥️  Command detected: {command}")

        if command["action"] != "none":
            result = execute_command(command)
            if result:
                # Tell Claude what happened so it responds naturally
                user_input = f"You just executed this action: {result}. Confirm it to the user naturally as MARKUS."


        live_keywords = [
            "news", "today", "right now", "currently",
            "latest", "war", "weather", "price", "score",
            "situation", "status", "open", "closed", "search"
        ]

        weather_keywords = ["weather", "temperature", "snow", "rain", 
                    "forecast", "cold", "warm", "outside", "walk"]
        
        context = ""


        if any(w in user_input.lower() for w in weather_keywords):
            from weather import get_weather
            city = extract_city(user_input)  # ← extracts city from speech
            print(f"🌤️  Fetching weather for: {city}")
            weather_data = get_weather(city)
            if weather_data:
                context = weather_data
            else:
                search_query = build_search_query(user_input)
                context = search_web(search_query)

        elif any(w in user_input.lower() for w in live_keywords):
            search_query = build_search_query(user_input)
            print(f"🔍 Searching: {search_query}")
            context = search_web(search_query)
            
        if context:
            user_input = f"""
User asked: {user_input}

Real time web results:
{context}

Answer based on above results naturally as MARKUS. Be direct and concise.
"""

        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=MARKUS_PERSONA,
            messages=conversation_history
        )

        reply = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": reply
        })
        return reply

    except Exception as e:
        print(f"❌ Brain error: {e}")
        return "I ran into an issue Deepu. Check the terminal."