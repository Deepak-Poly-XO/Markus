import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    # Default memory
    return {
        "user": {
            "name": "Deepu",
            "location": "Calgary"
        },
        "facts": {},
        "conversations": []
    }

def remove_fact(key):
    memory = load_memory()
    
    # Exact match first
    if key in memory["facts"]:
        del memory["facts"][key]
        save_memory(memory)
        print(f"🧠 Removed: {key}")
        return True, key

    # Fuzzy match — find closest key
    for existing_key in list(memory["facts"].keys()):
        if (key in existing_key or 
            existing_key in key or
            similar(key, existing_key)):
            del memory["facts"][existing_key]
            save_memory(memory)
            print(f"🧠 Removed: {existing_key} (matched from '{key}')")
            return True, existing_key

    return False, key

def similar(a, b):
    """Check if two strings are similar enough"""
    # Check if they share 70%+ characters
    shorter = min(len(a), len(b))
    matches = sum(c in b for c in a)
    return matches / max(len(a), 1) > 0.7

def clear_conversations():
    memory = load_memory()
    memory["conversations"] = []
    save_memory(memory)
    print("🧠 Conversation history cleared")

def clear_all_memory():
    memory = {
        "user": {"name": "Deepu", "location": "Calgary"},
        "facts": {},
        "conversations": []
    }
    save_memory(memory)
    print("🧠 All memory cleared")

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def add_fact(key, value):
    memory = load_memory()
    memory["facts"][key] = value
    save_memory(memory)
    print(f"🧠 Memory saved: {key} = {value}")

def save_conversation_summary(summary):
    memory = load_memory()
    memory["conversations"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary
    })
    # Keep only last 30 conversations
    memory["conversations"] = memory["conversations"][-30:]
    save_memory(memory)

def get_memory_context():
    memory = load_memory()
    context = f"User's name is {memory['user'].get('name', 'Deepu')}. "
    context += f"Location: {memory['user'].get('location', 'Calgary')}. "

    if memory["facts"]:
        context += "Known facts: "
        for k, v in memory["facts"].items():
            context += f"{k} = {v}. "

    if memory["conversations"]:
        context += "Recent conversations: "
        for conv in memory["conversations"][-5:]:
            context += f"[{conv['date']}] {conv['summary']}. "

    return context