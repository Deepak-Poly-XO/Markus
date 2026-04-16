import anthropic
import base64
import os
from PIL import ImageGrab
from config import API_KEY

client = anthropic.Anthropic(api_key=API_KEY)

def capture_screen():
    """Takes screenshot and returns as base64"""
    screenshot = ImageGrab.grab()
    
    # Save to temp file
    import tempfile
    temp_path = os.path.join(tempfile.gettempdir(), "markus_vision.png")
    screenshot.save(temp_path, "PNG")
    
    # Convert to base64
    with open(temp_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    os.remove(temp_path)
    return image_data

def see_screen(question="What do you see on this screen?"):
    """Send screenshot to Claude Vision and get description"""
    try:
        print("👁️ Capturing screen...")
        image_data = capture_screen()
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""You are MARKUS, an AI assistant analyzing the user's screen.
                            
User question: {question}

Answer naturally and concisely as if speaking out loud.
No markdown, no bullet points. Just speak naturally.
Focus on what's relevant to their question."""
                        }
                    ]
                }
            ]
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"❌ Vision error: {e}")
        return "I had trouble reading the screen sir."

def find_on_screen(what_to_find):
    """Find something specific on screen and return its location"""
    try:
        image_data = capture_screen()
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""Find '{what_to_find}' on this screen.
If found, respond with ONLY: FOUND:x,y where x and y are the approximate 
pixel coordinates of the center of the element.
If not found, respond with ONLY: NOT_FOUND
Nothing else."""
                        }
                    ]
                }
            ]
        )
        
        result = response.content[0].text.strip()
        
        if result.startswith("FOUND:"):
            coords = result.replace("FOUND:", "").split(",")
            x, y   = int(coords[0]), int(coords[1])
            return x, y
        
        return None
        
    except Exception as e:
        print(f"❌ Find error: {e}")
        return None

def click_on(what_to_click):
    """Find something on screen and click it"""
    import pyautogui
    
    coords = find_on_screen(what_to_click)
    if coords:
        x, y = coords
        pyautogui.click(x, y)
        return f"Clicked on {what_to_click} sir."
    return f"Could not find {what_to_click} on screen sir."

def read_screen_text():
    """Read all text visible on screen"""
    return see_screen("Read and summarize all the text you can see on this screen.")

def help_with_error():
    """Look at screen and help fix any errors"""
    return see_screen("""Look for any error messages, exceptions, or problems on this screen. 
    If you see an error, explain what it means and how to fix it in simple terms.
    If no error, describe what you see.""")