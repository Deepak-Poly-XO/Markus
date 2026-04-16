import anthropic
import os
from config import API_KEY

EVOLVE_MODEL = "claude-sonnet-4-6" 
client = anthropic.Anthropic(api_key=API_KEY)

EVOLVE_SYSTEM = """
You are a Python code generator for MARKUS AI running on Windows.
Write a single Python function that accomplishes the given task.

Rules:
- Function name must start with markus_
- Must return a string result message ending with "sir."
- No input parameters
- Windows only
- NEVER call driver.quit() or driver.close()

ALWAYS use this exact pattern for ALL browser tasks:

def markus_example():
    import self_evolve
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys

    driver = self_evolve.get_or_create_driver()
    wait   = WebDriverWait(driver, 15)

    driver.get("https://youtube.com")
    return "Done sir."

get_or_create_driver() handles everything automatically:
- If browser is open and alive → reuses it
- If browser was closed → creates fresh one
- Never crashes on dead sessions
NEVER manually check active_driver or create webdriver yourself.
ALWAYS use self_evolve.get_or_create_driver() — nothing else.

For searching on current page example:
def markus_search_benchpress():
    import self_evolve
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys

    driver = self_evolve.get_or_create_driver()
    wait   = WebDriverWait(driver, 15)

    try:
        search_box = wait.until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
        )
    except:
        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

    search_box.clear()
    search_box.send_keys("benchpress")
    search_box.send_keys(Keys.RETURN)
    return "Searched for benchpress sir."

For Windows Settings use ms-settings: URLs via subprocess.
For files use os module.
For apps use subprocess or os.startfile.
Return ONLY the raw Python function. No backticks. No explanation.
"""

def generate_capability(task):
    try:
        response = client.messages.create(
            model=EVOLVE_MODEL,
            max_tokens=1500,          # ← increase from 500 to 1500
            system=EVOLVE_SYSTEM,
            messages=[{"role": "user", "content": f"Write function to: {task}"}]
        )
        code = response.content[0].text.strip()
        code = code.replace("```python", "").replace("```", "").strip()

        # Validate code compiles before executing
        try:
            compile(code, "<string>", "exec")
            print("✅ Code validated")
        except SyntaxError as e:
            print(f"❌ Syntax error in generated code: {e}")
            print(f"📝 Bad code:\n{code}")
            return None

        return code

    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None

active_driver = None

def is_driver_alive():
    """Check if browser session is still valid"""
    global active_driver
    if active_driver is None:
        return False
    try:
        # Simple check — if this works, browser is alive
        _ = active_driver.current_url
        return True
    except:
        print("🔄 Browser session dead — clearing")
        active_driver = None
        return False

def get_or_create_driver():
    """Get existing driver or create fresh one"""
    global active_driver
    
    if is_driver_alive():
        print("🌐 Reusing existing browser")
        return active_driver

    # Create fresh browser
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    active_driver = driver
    print("🌐 Fresh browser created")
    return driver

def execute_capability(code):
    global active_driver

    try:
        # Inject active_driver into function scope
        setup_code = """
import sys
_driver_container = [None]
"""
        namespace = {
            "active_driver": active_driver,
            "_keep_alive": []
        }

        exec(code, namespace)

        func_name = [k for k in namespace.keys() if k.startswith("markus_")]
        if not func_name:
            return "Could not find function sir."

        result = namespace[func_name[0]]()

        # Grab driver from namespace after execution
        if "driver" in namespace:
            active_driver = namespace["driver"]
            print(f"🌐 Browser kept alive: {type(active_driver)}")
        elif "options" in namespace:
            # Driver might be inside local function scope
            # Search all values for WebDriver instance
            for val in namespace.values():
                try:
                    if hasattr(val, 'get') and hasattr(val, 'quit'):
                        active_driver = val
                        print(f"🌐 Browser captured and kept alive")
                        break
                except:
                    pass

        print(f"✅ Executed: {func_name[0]}")
        return result

    except Exception as e:
        print(f"❌ Execution error: {e}")
        return f"Ran into an error: {str(e)}"

def evolve_and_execute(task):
    print(f"🧬 Generating: {task}")
    code = generate_capability(task)
    if not code:
        return "Couldn't generate that capability sir."
    print(f"📝 Code:\n{code}\n")
    return execute_capability(code)  # ← no saving