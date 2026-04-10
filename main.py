import keyboard
import threading
import os
from listener import listen
from brain import think
from voice import speak
from ui import markus_ui

# Global flag
is_running = True

def shutdown():
    global is_running
    is_running = False  # ← Stop the loop first
    print("\n🔴 MARKUS offline.")
    markus_ui.add_message("SYSTEM", "Shutting down...")
    speak("Shutting down. Goodbye sir.")
    markus_ui.root.destroy()
    os._exit(0)

def activate_markus():
    if not is_running:
        return

    markus_ui.set_status("● LISTENING", "#00ff88")
    markus_ui.add_message("SYSTEM", "Listening...")

    text = listen()

    if not is_running:  # ← Check again after listening
        return

    if not text:
        markus_ui.set_status("● STANDBY", "#00aaff")
        return

    markus_ui.add_message("YOU", text)
    markus_ui.set_status("● THINKING", "#ffaa00")

    response = think(text)

    if not is_running:  # ← Check again after thinking
        return

    markus_ui.add_message("MARKUS", response)
    markus_ui.set_status("● SPEAKING", "#00aaff")
    speak(response)

    markus_ui.set_status("● STANDBY", "#00aaff")

def background():
    keyboard.add_hotkey('escape', shutdown)

    speak("MARKUS online. What are we planning today sir?")
    markus_ui.add_message("MARKUS", "Online. What are we planning today sir?")

    while is_running:  # ← Checks flag every loop
        activate_markus()

t = threading.Thread(target=background, daemon=True)
t.start()

markus_ui.run()