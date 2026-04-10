import threading
import os
import time
from listener import listen
from brain import think
from voice import speak
from ui import markus_ui
from wakeword import listen_for_wakeword
import webview

is_running = True

def shutdown():
    global is_running
    is_running = False
    from brain import summarize_and_save
    summarize_and_save()
    markus_ui.add_message("SYSTEM", "Shutting down...")
    speak("Shutdown command acknowledged. All active processes are now complete. Core systems disengaging. MARKUS… going offline.")
    try: webview.windows[0].destroy()
    except: pass
    os._exit(0)

def conversation_loop():
    """After wake word — keeps listening until 3 seconds of silence"""
    while is_running:
        text = listen(silence_limit=3)  # 3 second silence timeout

        # Nothing said — go back to wake word
        if not text or len(text.strip()) < 2:
            markus_ui.set_status("● STANDBY", "#00aaff")
            markus_ui.add_message("SYSTEM", "Returning to standby...")
            print("👂 Back to wake word...")
            return  # exits loop → wakeword resumes

        markus_ui.add_message("YOU", text)
        markus_ui.set_status("● THINKING", "#ffaa00")

        response = think(text)

        if not response:  # ← garbage detected
            markus_ui.set_status("● STANDBY", "#00aaff")
            return

        markus_ui.add_message("MARKUS", response)
        markus_ui.set_status("● SPEAKING", "#00aaff")
        speak(response)

        markus_ui.set_status("● LISTENING", "#00ff88")

def activate_markus():
    if not is_running:
        return

    from wakeword import speaking_event
    markus_ui.set_status("● LISTENING", "#00ff88")
    speak("Yes sir.")
    time.sleep(0.5)
    speaking_event.clear() 
    markus_ui.add_message("SYSTEM", "Activated.")

    # Keeps conversing until silence
    conversation_loop()

def background():
    import keyboard
    keyboard.add_hotkey('escape', shutdown)

    speak("Initializing system… Loading core modules… All systems operational. MARKUS is online.")
    markus_ui.add_message("MARKUS", "Online.")

    listen_for_wakeword(activate_markus)

t = threading.Thread(target=background, daemon=True)
t.start()

markus_ui.run()