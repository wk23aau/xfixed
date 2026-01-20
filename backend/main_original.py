import time
import os
import json
import shutil
import threading
import zipfile
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
except ImportError:
    print("Run: pip install pyautogui")
    pyautogui = None

try:
    import pyperclip
except ImportError:
    print("Run: pip install pyperclip")
    pyperclip = None

load_dotenv()

# Globals
stop_tab_monitor = False
pause_tab_monitor = False
driver_ref = None
target_tab_handle = None

SKILLS_PATH = os.path.abspath(".agent/skills")


def tab_monitor():
    global stop_tab_monitor, pause_tab_monitor, driver_ref, target_tab_handle
    print("Tab monitor started...")
    
    unwanted = ["acrobat", "adobe", "microsoftonline", "microsoft", "welcome"]
    
    while not stop_tab_monitor:
        if pause_tab_monitor:
            time.sleep(0.5)
            continue
            
        try:
            if driver_ref and target_tab_handle:
                handles = driver_ref.window_handles
                
                if len(handles) > 1:
                    for handle in handles[:]:
                        if handle == target_tab_handle:
                            continue
                        try:
                            driver_ref.switch_to.window(handle)
                            url = driver_ref.current_url.lower()
                            title = driver_ref.title.lower()
                            
                            if any(p in url or p in title for p in unwanted):
                                print(f"[Monitor] Closing: {url[:40]}")
                                driver_ref.close()
                        except:
                            pass
                    
                    try:
                        if target_tab_handle in driver_ref.window_handles:
                            driver_ref.switch_to.window(target_tab_handle)
                    except:
                        pass
        except:
            pass
        time.sleep(0.5)
    
    print("Tab monitor stopped.")


def start_tab_monitor(driver, handle=None):
    global driver_ref, stop_tab_monitor, target_tab_handle, pause_tab_monitor
    driver_ref = driver
    target_tab_handle = handle or driver.current_window_handle
    stop_tab_monitor = False
    pause_tab_monitor = False
    thread = threading.Thread(target=tab_monitor, daemon=True)
    thread.start()
    return thread


def pause_monitor():
    global pause_tab_monitor
    pause_tab_monitor = True


def resume_monitor():
    global pause_tab_monitor
    pause_tab_monitor = False


def stop_all():
    global stop_tab_monitor
    stop_tab_monitor = True


def handle_native_file_dialog(file_path):
    """Handle Windows native file dialog using Alt+N to focus filename field"""
    if not pyautogui:
        print("PyAutoGUI required")
        return False
    
    try:
        print(f"Handling dialog for: {file_path}")
        time.sleep(2)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        win_path = os.path.abspath(file_path).replace('/', '\\')
        print(f"Full path: {win_path}")
        
        # Focus filename field (Alt+N is Windows standard)
        print("Focusing filename field (Alt+N)...")
        pyautogui.hotkey('alt', 'n')
        time.sleep(0.5)
        
        # Select all existing text
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Paste path
        if pyperclip:
            pyperclip.copy(win_path)
            pyautogui.hotkey('ctrl', 'v')
            print("Pasted path")
        else:
            pyautogui.typewrite(win_path, interval=0.03)
            print("Typed path")
        
        time.sleep(0.5)
        
        # Submit
        print("Pressing Enter...")
        pyautogui.press('enter')
        
        time.sleep(3)
        print("Dialog handled successfully")
        return True
        
    except Exception as e:
        print(f"Dialog error: {e}")
        return False


def get_agent_skill(agent_id):
    """Read agent SKILL.md and extract info"""
    skill_path = os.path.join(SKILLS_PATH, agent_id, "SKILL.md")
    if not os.path.exists(skill_path):
        print(f"Skill not found: {skill_path}")
        return None
    
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse YAML frontmatter
    name = agent_id
    description = ""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"\'')
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"\'')
    
    return {
        "id": agent_id,
        "name": name,
        "description": description,
        "skill_content": content,
        "skill_path": skill_path
    }


def create_agent_zip(agent_id, output_dir="temp_agents"):
    """Create .agent.zip for a specific agent"""
    skill = get_agent_skill(agent_id)
    if not skill:
        return None
    
    # Create temp directory
    os.makedirs(output_dir, exist_ok=True)
    agent_dir = os.path.join(output_dir, agent_id)
    os.makedirs(agent_dir, exist_ok=True)
    
    # Create core_instructions.md from SKILL.md
    core_path = os.path.join(agent_dir, "core_instructions.md")
    with open(core_path, "w", encoding="utf-8") as f:
        f.write(skill["skill_content"])
    
    # Create other files
    files = {
        "input.md": "# Input\n\nAwaiting input...\n",
        "output.md": "# Output Format\n\nRespond ONLY in this format:\n```\nSTATUS: [READY|PROCESSING|COMPLETE|ERROR]\nTASK_ID: [task identifier]\nRESULT: [your response]\n```\n",
        "memory.json": "{}"
    }
    
    for fname, content in files.items():
        fpath = os.path.join(agent_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
    
    # Create zip
    zip_path = os.path.join(output_dir, f"{agent_id}.agent.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in ["core_instructions.md", "input.md", "output.md", "memory.json"]:
            zf.write(os.path.join(agent_dir, fname), fname)
    
    print(f"Created: {zip_path}")
    return zip_path


def upload_zip(driver, zip_path):
    """Upload a zip file via app UI"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        print(f"Uploading zip: {zip_path}")
        time.sleep(2)
        
        # Find Add button
        add_btn = None
        for xpath in [
            "//button[contains(@aria-label, 'Add')]",
            "//button[contains(@aria-label, 'Import')]",
            "//button[.//span[text()='add']]",
        ]:
            try:
                els = driver.find_elements(By.XPATH, xpath)
                for el in els:
                    if el.is_displayed():
                        add_btn = el
                        break
                if add_btn:
                    break
            except:
                pass
        
        if not add_btn:
            print("Add button not found")
            return False
        
        add_btn.click()
        print("Clicked Add")
        time.sleep(1)
        
        # Click Upload Zip
        zip_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Upload Zip')]")
        ))
        zip_item.click()
        print("Clicked Upload Zip")
        
        time.sleep(2)
        return handle_native_file_dialog(zip_path)
        
    except Exception as e:
        print(f"Upload error: {e}")
        return False
    finally:
        resume_monitor()


def upload_files(driver, files):
    """Upload individual files via 'Upload files' menu option"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        for file_name in files:
            file_path = os.path.abspath(file_name)
            if not os.path.exists(file_path):
                print(f"File not found, skipping: {file_path}")
                continue
                
            print(f"Uploading: {file_name}")
            time.sleep(1)
            
            # Find Add button
            add_btn = None
            for xpath in [
                "//button[contains(@aria-label, 'Add')]",
                "//button[contains(@aria-label, 'Import')]",
                "//button[.//span[text()='add']]",
            ]:
                try:
                    els = driver.find_elements(By.XPATH, xpath)
                    for el in els:
                        if el.is_displayed():
                            add_btn = el
                            break
                    if add_btn:
                        break
                except:
                    pass
            
            if not add_btn:
                print("Add button not found")
                continue
            
            try:
                add_btn.click()
            except:
                driver.execute_script("arguments[0].click();", add_btn)
            print("Clicked Add")
            time.sleep(1)
            
            # Click "Upload files" (not "Upload Zip")
            files_item = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Upload files') or contains(text(), 'Upload file')]")
            ))
            try:
                files_item.click()
            except:
                driver.execute_script("arguments[0].click();", files_item)
            print("Clicked Upload files")
            
            time.sleep(2)
            
            # Handle native file dialog
            if not handle_native_file_dialog(file_path):
                print(f"Failed to upload: {file_name}")
            else:
                print(f"Uploaded: {file_name}")
            
            time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"Upload files error: {e}")
        return False
    finally:
        resume_monitor()


def set_system_instructions(driver, instructions):
    """Set system instructions via advanced settings"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        print("Setting system instructions...")
        
        # Step 1: Click "System instructions" button in advanced settings panel
        # First we need to open Advanced Settings if not already open
        try:
            adv_settings_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'settings') or contains(@aria-label, 'Settings')]")
            adv_settings_btn.click()
            print("Opened Advanced settings panel")
            time.sleep(2)
        except:
            print("Advanced settings panel may already be open or button not found")
        
        # Step 2: Click "System instructions" card button
        si_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-test-id='instructions-button']")
        ))
        si_button.click()
        print("Clicked System instructions button")
        time.sleep(2)
        
        # Step 3: Find the textarea with id="custom-si-textarea"
        sys_textarea = wait.until(EC.visibility_of_element_located(
            (By.ID, "custom-si-textarea")
        ))
        sys_textarea.click()
        time.sleep(0.3)
        sys_textarea.clear()
        time.sleep(0.3)
        
        # Paste instructions
        if pyperclip:
            pyperclip.copy(instructions)
            pyautogui.hotkey('ctrl', 'v')
        else:
            sys_textarea.send_keys(instructions)
        
        print("Entered system instructions")
        time.sleep(1)
        
        # Step 4: Click "Save changes" button
        save_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'ms-button-primary') and contains(., 'Save changes')]")
        ))
        save_btn.click()
        print("Clicked Save changes")
        time.sleep(2)
        
        # Step 5: Close the panels using Escape key (most reliable)
        print("Closing panels with Escape...")
        pyautogui.press('escape')
        time.sleep(0.5)
        pyautogui.press('escape')
        time.sleep(0.5)
        pyautogui.press('escape')
        time.sleep(1)
        
        print("System instructions saved!")
        return True
        
    except Exception as e:
        print(f"System instructions error: {e}")
        # Try to close any open dialogs
        try:
            pyautogui.press('escape')
        except:
            pass
        return False
    finally:
        resume_monitor()


def save_app(driver, app_name):
    """Save the app with a specific name"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        print(f"Saving app as: {app_name}")
        
        # Click Save button (use JS click to bypass overlays)
        save_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[@aria-label='Save app']")
        ))
        try:
            save_btn.click()
        except:
            driver.execute_script("arguments[0].click();", save_btn)
        print("Clicked Save button")
        time.sleep(2)
        
        # Wait for rename dialog and enter name
        name_input = wait.until(EC.visibility_of_element_located(
            (By.ID, "name-input")
        ))
        name_input.clear()
        name_input.send_keys(app_name)
        print(f"Entered name: {app_name}")
        time.sleep(0.5)
        
        # Click Save in dialog (use JS click to bypass overlays)
        dialog_save_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//mat-dialog-actions//button[contains(@class, 'ms-button-primary')]")
        ))
        try:
            dialog_save_btn.click()
        except:
            driver.execute_script("arguments[0].click();", dialog_save_btn)
        print("Clicked Save in dialog")
        
        time.sleep(3)
        print("App saved successfully!")
        return True
        
    except Exception as e:
        print(f"Save app error: {e}")
        return False
    finally:
        resume_monitor()


def get_app_url(driver):
    """Get the current app URL after saving"""
    time.sleep(2)
    url = driver.current_url
    print(f"App URL: {url}")
    return url


def save_agent_url(agent_id, url, filename="agents.json"):
    """Save the agent URL to a JSON file"""
    try:
        filepath = os.path.abspath(filename)
        
        agents = {}
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    agents = json.load(f)
                except:
                    agents = {}
        
        agents[agent_id] = {
            "url": url,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(agents, f, indent=2)
        
        print(f"Saved agent '{agent_id}' URL to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving agent URL: {e}")
        return False


def send_chat_message(driver, message):
    """Type a message in the chatbox and send it"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        print(f"Sending message...")
        
        # Find the chatbox textarea
        chatbox = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.input-container textarea")
        ))
        try:
            chatbox.click()
        except:
            driver.execute_script("arguments[0].click();", chatbox)
        time.sleep(0.5)
        
        # Paste message (faster than typing)
        if pyperclip:
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
        else:
            chatbox.send_keys(message)
        
        print("Typed message")
        time.sleep(1)
        
        # Click send button (use JS click to bypass overlays)
        send_btn = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.send-button[aria-label='Send']")
        ))
        try:
            send_btn.click()
        except:
            driver.execute_script("arguments[0].click();", send_btn)
        print("Clicked Send")
        
        time.sleep(3)
        print("Message sent!")
        return True
        
    except Exception as e:
        print(f"Send message error: {e}")
        return False
    finally:
        resume_monitor()


def select_model(driver, model_name="Gemini 3 Pro Preview"):
    """Select the AI model from Advanced settings dropdown"""
    wait = WebDriverWait(driver, 15)
    pause_monitor()
    
    try:
        print(f"Selecting model: {model_name}")
        
        # Step 1: Open Advanced settings panel
        try:
            adv_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'settings') or contains(@aria-label, 'Settings')]")
            driver.execute_script("arguments[0].click();", adv_btn)
            print("Opened Advanced settings panel")
            time.sleep(2)
        except:
            print("Could not open Advanced settings")
        
        # Step 2: Click on the model selector dropdown (inside Advanced settings)
        model_dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "mat-select[aria-label='Select the model for the code assistant']")
        ))
        driver.execute_script("arguments[0].click();", model_dropdown)
        print("Opened model dropdown")
        time.sleep(1)
        
        # Step 3: Select the model option
        model_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//mat-option[contains(., '{model_name}')]")
        ))
        driver.execute_script("arguments[0].click();", model_option)
        print(f"Selected: {model_name}")
        time.sleep(1)
        
        # Step 4: Close the panel with Escape
        print("Closing Advanced settings...")
        pyautogui.press('escape')
        time.sleep(0.5)
        pyautogui.press('escape')
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"Model selection error: {e}")
        pyautogui.press('escape')
        time.sleep(0.5)
        pyautogui.press('escape')
        return False
    finally:
        resume_monitor()


def spawn_agent(driver, agent_id):
    """Spawn a single agent: create zip, upload, configure, save"""
    print(f"\n{'='*50}")
    print(f"SPAWNING AGENT: {agent_id}")
    print(f"{'='*50}")
    
    # Get agent skill info
    skill = get_agent_skill(agent_id)
    if not skill:
        print(f"Failed to get skill for {agent_id}")
        return False
    
    # Create agent zip
    zip_path = create_agent_zip(agent_id)
    if not zip_path:
        print(f"Failed to create zip for {agent_id}")
        return False
    
    # Navigate to new app page
    url = "https://aistudio.google.com/apps/bundled/blank?showAssistant=true&showCode=true"
    print(f"Navigating to: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Select Gemini 3 Pro Preview model
    select_model(driver, "Gemini 3 Pro Preview")
    
    # Upload the agent zip
    if not upload_zip(driver, zip_path):
        print(f"Failed to upload zip for {agent_id}")
        return False
    
    # Upload xagent.zip (the project these agents work on)
    # Upload core.txt (the project documentation these agents work on)
    core_txt = os.path.abspath("core.txt")
    if os.path.exists(core_txt):
        print(f"Uploading project: core.txt")
        upload_files(driver, ["core.txt"])
    else:
        print(f"core.txt not found, skipping project upload")
    
    # Set system instructions from SKILL.md
    set_system_instructions(driver, skill["skill_content"])
    
    # Save app with agent name
    app_name = f"AGENT: {agent_id}"
    save_app(driver, app_name)
    
    # Get and save URL
    app_url = get_app_url(driver)
    save_agent_url(agent_id, app_url)
    
    # Send initialization message
    init_message = f"""First, analyze core.txt to understand the full project context and architecture.

Then read your core_instructions.md file to understand your specific role.

You are {skill['name']}.

{skill['description']}

Now wear the hat of your assigned role. Take on this role completely and act as required.

CRITICAL: You must write ALL your responses directly to the output.md file, NOT in this chat window.

When you have output, edit the output.md file with your response in this format:
```
STATUS: [READY|PROCESSING|COMPLETE|ERROR]
TASK_ID: [task identifier]
RESULT: [your response]
```

DO NOT respond in the chat. Write to output.md file ONLY.

Confirm you understand by editing output.md with STATUS: READY."""
    
    send_chat_message(driver, init_message)
    
    print(f"\nAgent {agent_id} spawned successfully!")
    return True


def login_to_google(driver, wait):
    email = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")

    if not email or not password:
        print("No credentials in .env")
        return

    pause_monitor()

    try:
        print("Entering email...")
        email_field = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//input[@type="email"]')
        ))
        email_field.clear()
        email_field.send_keys(email)
        email_field.send_keys("\n")
        
        time.sleep(3)

        print("Entering password...")
        password_field = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//input[@type="password"]')
        ))
        password_field.clear()
        password_field.send_keys(password)
        password_field.send_keys("\n")
        
        print("Waiting for login...")
        wait.until(lambda d: "accounts.google.com" not in d.current_url)
        print("Login successful!")

    except Exception as e:
        print(f"Login error: {e}")
        print("Please login manually...")
        try:
            WebDriverWait(driver, 120).until(
                lambda d: "aistudio.google.com" in d.current_url
            )
        except:
            pass
    finally:
        resume_monitor()


def main():
    extension_path = os.path.abspath("extension")
    profile_path = os.path.abspath("chrome_profile")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--load-extension={extension_path}")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    print(f"Extension: {extension_path}")
    print(f"Profile: {profile_path}")
    
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("Waiting for startup...")
        time.sleep(8)
        
        # Navigate to AI Studio
        url = "https://aistudio.google.com/apps/bundled/blank?showAssistant=true&showCode=true"
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        start_tab_monitor(driver)
        
        # Login if needed
        if "accounts.google.com" in driver.current_url:
            login_to_google(driver, wait)
        
        time.sleep(3)
        
        # Spawn a single agent (CTO-001 as example)
        # You can modify this to spawn multiple agents
        agent_id = "CTO-001"
        spawn_agent(driver, agent_id)

        print("\nBrowser ready. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_all()
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
