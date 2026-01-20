import time
import os
import json
import shutil
import threading
import zipfile
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException

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
agent_handles = {}  # {agent_id: window_handle} - track each agent's tab

# =============================================================================
# P12: Browser Initialization Function
# - Required by ensure_browser() for browser recovery
# =============================================================================
def init_driver():
    """Initialize Chrome WebDriver with undetected-chromedriver"""
    extension_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extension"))
    profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chrome_profile"))
    
    options = uc.ChromeOptions()
    options.add_argument(f"--load-extension={extension_path}")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    print("[init_driver] Launching Chrome...")
    driver = uc.Chrome(options=options)
    print("[init_driver] Chrome launched successfully")
    
    return driver

# =============================================================================
# P12: Browser Health Check and Recovery
# - is_browser_alive(): Check if browser is still running
# - ensure_browser(): Restart browser if dead, clear stale handles
# =============================================================================
def is_browser_alive():
    """Check if browser is still running"""
    global driver_ref
    
    if driver_ref is None:
        return False
    
    try:
        # Try to access a property - will fail if browser closed
        _ = driver_ref.window_handles
        return True
    except Exception:
        return False

def ensure_browser():
    """Ensure browser is running, start if needed. Returns driver or None."""
    global driver_ref, agent_handles
    
    if is_browser_alive():
        return driver_ref
    
    print("[P12] Browser not running, attempting recovery...")
    
    # Clean up stale references
    driver_ref = None
    agent_handles.clear()  # All handles are invalid now
    
    try:
        # Start new browser
        driver_ref = init_driver()
        
        # Warm up with AI Studio
        driver_ref.get("https://aistudio.google.com")
        time.sleep(3)
        
        print("[P12] Browser recovered successfully")
        return driver_ref
    except Exception as e:
        print(f"[P12] Failed to recover browser: {e}")
        return None

SKILLS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agent", "skills"))


# =============================================================================
# P1 Phase 2: Dual Logging System
# - File (logs/xapply.log): DEBUG level, JSON format, everything
# - Terminal: INFO level, important flow steps only
# =============================================================================
import sys
import platform
from datetime import datetime

class Logger:
    """Dual-output logger: JSON file (DEBUG) + Terminal (INFO)"""
    
    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
    
    def __init__(self, log_dir="logs", log_file="xapply.log"):
        self.log_dir = os.path.join(os.path.dirname(__file__), log_dir)
        self.log_path = os.path.join(self.log_dir, log_file)
        self._ensure_log_dir()
        self._log_startup()
    
    def _ensure_log_dir(self):
        """Create logs/ directory if it doesn't exist"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _write_file(self, entry: dict):
        """Append JSON entry to log file"""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[Logger] File write error: {e}")
    
    def _log_startup(self):
        """Log startup info with system details"""
        self.log("INFO", "STARTUP", "Backend starting", {
            "python": platform.python_version(),
            "os": platform.system(),
            "cwd": os.getcwd()
        })
    
    def log(self, level: str, category: str, message: str, data: dict = None):
        """
        Log a message with dual output.
        
        Args:
            level: DEBUG, INFO, WARNING, ERROR
            category: STARTUP, CHROME, NAVIGATION, AGENT, etc.
            message: Human-readable message
            data: Optional dict with extra info
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "timestamp": timestamp,
            "level": level,
            "category": category,
            "message": message
        }
        if data:
            entry["data"] = data
        
        # Always write to file (DEBUG level = everything)
        self._write_file(entry)
        
        # Only print INFO+ to terminal
        if self.LEVELS.get(level, 0) >= self.LEVELS["INFO"]:
            print(f"[{category}] {message}")
    
    def debug(self, category: str, message: str, data: dict = None):
        self.log("DEBUG", category, message, data)
    
    def info(self, category: str, message: str, data: dict = None):
        self.log("INFO", category, message, data)
    
    def warning(self, category: str, message: str, data: dict = None):
        self.log("WARNING", category, message, data)
    
    def error(self, category: str, message: str, data: dict = None):
        self.log("ERROR", category, message, data)


# Initialize global logger
logger = Logger()


# =============================================================================
# P5 Phase 10: Agent SQLite Database
# - Persists agent info across restarts (drive_url, email, files)
# - Status resets to 'inactive' on every startup
# - agent_handles (memory) is always {} on startup
# =============================================================================
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "agents.db")

def init_agent_db():
    """Initialize SQLite database for agent persistence"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create agents table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            status TEXT DEFAULT 'inactive',
            drive_url TEXT,
            google_email TEXT,
            files_uploaded TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reset ALL agent statuses to 'inactive' on startup
    cursor.execute("UPDATE agents SET status = 'inactive'")
    
    conn.commit()
    conn.close()
    logger.info("AGENT", "Database initialized", {"path": DB_PATH})

def db_get_agent(agent_id):
    """Get agent from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def db_upsert_agent(agent_id, name=None, description=None, status=None, 
                    drive_url=None, google_email=None, files_uploaded=None):
    """Insert or update agent in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
    exists = cursor.fetchone() is not None
    
    if exists:
        # Build UPDATE statement dynamically
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        if drive_url is not None:
            updates.append("drive_url = ?")
            values.append(drive_url)
        if google_email is not None:
            updates.append("google_email = ?")
            values.append(google_email)
        if files_uploaded is not None:
            updates.append("files_uploaded = ?")
            values.append(files_uploaded)
        
        if updates:
            values.append(agent_id)
            cursor.execute(f"UPDATE agents SET {', '.join(updates)} WHERE id = ?", values)
    else:
        # INSERT new agent
        cursor.execute('''
            INSERT INTO agents (id, name, description, status, drive_url, google_email, files_uploaded)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (agent_id, name, description, status or 'inactive', drive_url, google_email, files_uploaded))
    
    conn.commit()
    conn.close()

def db_get_all_agents():
    """Get all agents from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize database on module load
init_agent_db()


def tab_monitor():
    """P4 Phase 8: Background tab monitor - closes unwanted popups"""
    # breakpoint()  # DEBUG: Tab monitor loop start
    global stop_tab_monitor, pause_tab_monitor, driver_ref, target_tab_handle
    logger.info("TAB", "Tab monitor started")
    
    unwanted = ["acrobat", "adobe", "microsoftonline", "microsoft", "welcome"]
    logger.debug("TAB", "Unwanted patterns configured", {"patterns": unwanted})
    
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
                                logger.info("TAB", "Closing unwanted tab", {"url": url[:50]})
                                driver_ref.close()
                        except Exception as e:
                            logger.debug("TAB", "Error checking handle", {"error": str(e)})
                    
                    try:
                        if target_tab_handle in driver_ref.window_handles:
                            driver_ref.switch_to.window(target_tab_handle)
                    except:
                        pass
        except Exception as e:
            logger.debug("TAB", "Monitor loop error", {"error": str(e)})
        time.sleep(0.5)
    
    logger.info("TAB", "Tab monitor stopped")
    # breakpoint()  # DEBUG: Tab monitor stopped


def start_tab_monitor(driver, handle=None):
    # breakpoint()  # DEBUG: Starting tab monitor
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
    # breakpoint()  # DEBUG: Native file dialog handler
    print(f"[DEBUG] handle_native_file_dialog: Starting for {file_path}")
    if not pyautogui:
        print("PyAutoGUI required")
        return False
    
    try:
        print(f"Handling dialog for: {file_path}")
        print(f"[DEBUG] handle_native_file_dialog: Waiting 2s for dialog")
    # breakpoint()  # DEBUG: Before dialog wait
        time.sleep(2)
        
        print(f"[DEBUG] handle_native_file_dialog: Checking file exists")
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
    # breakpoint()  # DEBUG: File not found
            return False
        
        win_path = os.path.abspath(file_path).replace('/', '\\')
        print(f"Full path: {win_path}")
        print(f"[DEBUG] handle_native_file_dialog: Converted path to Windows format")
    # breakpoint()  # DEBUG: Path converted
        
        # Focus filename field (Alt+N is Windows standard)
        print("Focusing filename field (Alt+N)...")
        print(f"[DEBUG] handle_native_file_dialog: Sending Alt+N hotkey")
    # breakpoint()  # DEBUG: Before Alt+N
        pyautogui.hotkey('alt', 'n')
        time.sleep(0.5)
        print(f"[DEBUG] handle_native_file_dialog: Alt+N sent")
        
        # Select all existing text
        print(f"[DEBUG] handle_native_file_dialog: Sending Ctrl+A")
    # breakpoint()  # DEBUG: Before Ctrl+A
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        print(f"[DEBUG] handle_native_file_dialog: Ctrl+A sent")
        
        # Paste path
        print(f"[DEBUG] handle_native_file_dialog: Pasting/typing path")
    # breakpoint()  # DEBUG: Before paste
        if pyperclip:
            pyperclip.copy(win_path)
            pyautogui.hotkey('ctrl', 'v')
            print("Pasted path")
            print(f"[DEBUG] handle_native_file_dialog: Clipboard paste complete")
        else:
            pyautogui.typewrite(win_path, interval=0.03)
            print("Typed path")
            print(f"[DEBUG] handle_native_file_dialog: Typewrite complete")
        
        time.sleep(0.5)
        
        # Submit
        print("Pressing Enter...")
        print(f"[DEBUG] handle_native_file_dialog: Sending Enter key")
    # breakpoint()  # DEBUG: Before Enter
        pyautogui.press('enter')
        
        print(f"[DEBUG] handle_native_file_dialog: Waiting 3s for dialog close")
        time.sleep(3)
        print("Dialog handled successfully")
    # breakpoint()  # DEBUG: Dialog complete
        return True
        
    except Exception as e:
        print(f"Dialog error: {e}")
        print(f"[DEBUG] handle_native_file_dialog: EXCEPTION: {e}")
    # breakpoint()  # DEBUG: Dialog error
        return False


def get_agent_skill(agent_id):
    """Read agent SKILL.md and extract info"""
    # breakpoint()  # DEBUG: Loading agent skill
    print(f"[DEBUG] get_agent_skill: Loading skill for {agent_id}")
    skill_path = os.path.join(SKILLS_PATH, agent_id, "SKILL.md")
    print(f"[DEBUG] get_agent_skill: Skill path: {skill_path}")
    # breakpoint()  # DEBUG: Skill path resolved
    
    if not os.path.exists(skill_path):
        print(f"Skill not found: {skill_path}")
        print(f"[DEBUG] get_agent_skill: File does not exist")
    # breakpoint()  # DEBUG: Skill not found
        return None
    
    print(f"[DEBUG] get_agent_skill: Reading file...")
    # breakpoint()  # DEBUG: Before file read
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"[DEBUG] get_agent_skill: File read, {len(content)} bytes")
    # breakpoint()  # DEBUG: After file read
    
    # Parse YAML frontmatter
    name = agent_id
    description = ""
    print(f"[DEBUG] get_agent_skill: Parsing YAML frontmatter")
    if content.startswith("---"):
        print(f"[DEBUG] get_agent_skill: Found frontmatter delimiter")
    # breakpoint()  # DEBUG: Parsing frontmatter
        parts = content.split("---", 2)
        print(f"[DEBUG] get_agent_skill: Split into {len(parts)} parts")
        if len(parts) >= 3:
            frontmatter = parts[1]
            print(f"[DEBUG] get_agent_skill: Frontmatter: {frontmatter[:100]}...")
            for line in frontmatter.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"\'')
                    print(f"[DEBUG] get_agent_skill: Found name: {name}")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"\'')
                    print(f"[DEBUG] get_agent_skill: Found description: {description[:50]}...")
    
    result = {
        "id": agent_id,
        "name": name,
        "description": description,
        "skill_content": content,
        "skill_path": skill_path
    }
    print(f"[DEBUG] get_agent_skill: Returning skill object")
    # breakpoint()  # DEBUG: Skill loaded successfully
    return result


def create_agent_zip(agent_id, output_dir="temp_agents"):
    """Create .agent.zip for a specific agent"""
    # breakpoint()  # DEBUG: Creating agent zip package
    print(f"[DEBUG] create_agent_zip: Starting for {agent_id}")
    print(f"[DEBUG] create_agent_zip: Output dir: {output_dir}")
    
    print(f"[DEBUG] create_agent_zip: Getting agent skill")
    # breakpoint()  # DEBUG: Before get_agent_skill call
    skill = get_agent_skill(agent_id)
    if not skill:
        print(f"[DEBUG] create_agent_zip: No skill found, returning None")
    # breakpoint()  # DEBUG: Skill not found
        return None
    print(f"[DEBUG] create_agent_zip: Skill loaded: {skill['name']}")
    # breakpoint()  # DEBUG: After get_agent_skill call
    
    # Create temp directory
    print(f"[DEBUG] create_agent_zip: Creating directories")
    # breakpoint()  # DEBUG: Before directory creation
    os.makedirs(output_dir, exist_ok=True)
    agent_dir = os.path.join(output_dir, agent_id)
    os.makedirs(agent_dir, exist_ok=True)
    print(f"[DEBUG] create_agent_zip: Agent dir: {agent_dir}")
    
    # Create core_instructions.md from SKILL.md
    core_path = os.path.join(agent_dir, "core_instructions.md")
    print(f"[DEBUG] create_agent_zip: Writing core_instructions.md")
    # breakpoint()  # DEBUG: Before writing core_instructions
    with open(core_path, "w", encoding="utf-8") as f:
        f.write(skill["skill_content"])
    print(f"[DEBUG] create_agent_zip: Wrote {len(skill['skill_content'])} bytes")
    
    # Create other files
    files = {
        "input.md": "# Input\n\nAwaiting input...\n",
        "output.md": "# Output Format\n\nRespond ONLY in this format:\n```\nSTATUS: [READY|PROCESSING|COMPLETE|ERROR]\nTASK_ID: [task identifier]\nRESULT: [your response]\n```\n",
        "memory.json": "{}"
    }
    
    print(f"[DEBUG] create_agent_zip: Writing {len(files)} additional files")
    # breakpoint()  # DEBUG: Before writing other files
    for fname, content in files.items():
        fpath = os.path.join(agent_dir, fname)
        print(f"[DEBUG] create_agent_zip: Writing {fname}")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"[DEBUG] create_agent_zip: All files written")
    
    # Create zip
    zip_path = os.path.join(output_dir, f"{agent_id}.agent.zip")
    print(f"[DEBUG] create_agent_zip: Creating zip at {zip_path}")
    # breakpoint()  # DEBUG: Before zip creation
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in ["core_instructions.md", "input.md", "output.md", "memory.json"]:
            full_path = os.path.join(agent_dir, fname)
            print(f"[DEBUG] create_agent_zip: Adding {fname} to zip")
            zf.write(full_path, fname)
    
    print(f"Created: {zip_path}")
    print(f"[DEBUG] create_agent_zip: Zip created successfully")
    # breakpoint()  # DEBUG: Zip creation complete
    return zip_path


def upload_zip(driver, zip_path):
    """Upload a zip file via app UI"""
    # breakpoint()  # DEBUG: Zip upload workflow start
    print(f"[DEBUG] upload_zip: Starting upload for {zip_path}")
    wait = WebDriverWait(driver, 15)
    print(f"[DEBUG] upload_zip: Pausing tab monitor")
    pause_monitor()
    
    try:
        print(f"Uploading zip: {zip_path}")
        print(f"[DEBUG] upload_zip: Waiting 2s for page stability")
    # breakpoint()  # DEBUG: Before initial wait
        time.sleep(2)
        
        # Find Add button
        print(f"[DEBUG] upload_zip: Searching for Add button")
    # breakpoint()  # DEBUG: Before button search
        add_btn = None
        for xpath in [
            "//button[contains(@aria-label, 'Add')]",
            "//button[contains(@aria-label, 'Import')]",
            "//button[.//span[text()='add']]",
        ]:
            try:
                print(f"[DEBUG] upload_zip: Trying xpath: {xpath}")
                els = driver.find_elements(By.XPATH, xpath)
                print(f"[DEBUG] upload_zip: Found {len(els)} elements")
                for el in els:
                    if el.is_displayed():
                        add_btn = el
                        print(f"[DEBUG] upload_zip: Found displayed Add button")
                        break
                if add_btn:
                    break
            except Exception as e:
                print(f"[DEBUG] upload_zip: Xpath error: {e}")
                pass
        
        if not add_btn:
            print("Add button not found")
            print(f"[DEBUG] upload_zip: FAILED - Add button not found")
    # breakpoint()  # DEBUG: Add button not found
            return False
        
        print(f"[DEBUG] upload_zip: Clicking Add button")
    # breakpoint()  # DEBUG: Before clicking Add
        add_btn.click()
        print("Clicked Add")
        print(f"[DEBUG] upload_zip: Add button clicked")
        time.sleep(1)
        
        # Click Upload Zip
        print(f"[DEBUG] upload_zip: Waiting for Upload Zip menu item")
    # breakpoint()  # DEBUG: Before finding Upload Zip
        zip_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Upload Zip')]")
        ))
        print(f"[DEBUG] upload_zip: Found Upload Zip item")
    # breakpoint()  # DEBUG: Before clicking Upload Zip
        zip_item.click()
        print("Clicked Upload Zip")
        print(f"[DEBUG] upload_zip: Upload Zip clicked")
        
        print(f"[DEBUG] upload_zip: Waiting 2s for file dialog")
        time.sleep(2)
        print(f"[DEBUG] upload_zip: Calling handle_native_file_dialog")
    # breakpoint()  # DEBUG: Before file dialog
        result = handle_native_file_dialog(zip_path)
        print(f"[DEBUG] upload_zip: File dialog result: {result}")
    # breakpoint()  # DEBUG: After file dialog
        return result
        
    except Exception as e:
        print(f"Upload error: {e}")
        print(f"[DEBUG] upload_zip: EXCEPTION: {e}")
    # breakpoint()  # DEBUG: Upload error
        return False
    finally:
        print(f"[DEBUG] upload_zip: Resuming tab monitor")
        resume_monitor()


def upload_files(driver, files):
    """Upload individual files via 'Upload files' menu option"""
    # breakpoint()  # DEBUG: File upload workflow
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


def set_system_instructions(driver, instructions, skip_open=False):
    """Set system instructions via advanced settings
    
    Args:
        skip_open: If True, skip opening settings panel (already open from select_model)
    """
    # breakpoint()  # DEBUG: System instructions workflow start
    print(f"[DEBUG] set_system_instructions: Starting")
    print(f"[DEBUG] set_system_instructions: Instructions length: {len(instructions)} chars")
    wait = WebDriverWait(driver, 15)
    print(f"[DEBUG] set_system_instructions: Pausing tab monitor")
    pause_monitor()
    
    try:
        print("Setting system instructions...")
        
        # Step 1: Open Advanced Settings if not already open
        if not skip_open:
            print(f"[DEBUG] set_system_instructions: Step 1 - Opening advanced settings")
            try:
                adv_settings_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'settings') or contains(@aria-label, 'Settings')]")
                print(f"[DEBUG] set_system_instructions: Found settings button")
                adv_settings_btn.click()
                print("Opened Advanced settings panel")
                print(f"[DEBUG] set_system_instructions: Clicked settings button")
                time.sleep(2)
            except Exception as e:
                print("Advanced settings panel may already be open or button not found")
                print(f"[DEBUG] set_system_instructions: Settings button error: {e}")
        else:
            print("[DEBUG] set_system_instructions: Skipping open (panel already open)")
        
        # Step 2: Click "System instructions" card button
        print(f"[DEBUG] set_system_instructions: Step 2 - Finding SI button")
    # breakpoint()  # DEBUG: Before finding SI button
        si_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-test-id='instructions-button']")
        ))
        print(f"[DEBUG] set_system_instructions: Found SI button")
    # breakpoint()  # DEBUG: Before clicking SI button
        si_button.click()
        print("Clicked System instructions button")
        print(f"[DEBUG] set_system_instructions: SI button clicked")
        time.sleep(2)
        
        # Step 3: Find the textarea with id="custom-si-textarea"
        print(f"[DEBUG] set_system_instructions: Step 3 - Finding textarea")
    # breakpoint()  # DEBUG: Before finding textarea
        sys_textarea = wait.until(EC.visibility_of_element_located(
            (By.ID, "custom-si-textarea")
        ))
        print(f"[DEBUG] set_system_instructions: Found textarea")
    # breakpoint()  # DEBUG: Before clicking textarea
        sys_textarea.click()
        print(f"[DEBUG] set_system_instructions: Clicked textarea")
        time.sleep(0.3)
        print(f"[DEBUG] set_system_instructions: Clearing textarea")
        sys_textarea.clear()
        print(f"[DEBUG] set_system_instructions: Textarea cleared")
        time.sleep(0.3)
        
        # Paste instructions
        print(f"[DEBUG] set_system_instructions: Pasting instructions")
    # breakpoint()  # DEBUG: Before paste
        if pyperclip:
            pyperclip.copy(instructions)
            pyautogui.hotkey('ctrl', 'v')
            print(f"[DEBUG] set_system_instructions: Pasted via clipboard")
        else:
            sys_textarea.send_keys(instructions)
            print(f"[DEBUG] set_system_instructions: Typed via send_keys")
        
        print("Entered system instructions")
        print(f"[DEBUG] set_system_instructions: Instructions entered")
    # breakpoint()  # DEBUG: After paste
        time.sleep(1)
        
        # Step 4: Click "Save changes" button
        print(f"[DEBUG] set_system_instructions: Step 4 - Finding Save button")
    # breakpoint()  # DEBUG: Before finding Save button
        save_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'ms-button-primary') and contains(., 'Save changes')]")
        ))
        print(f"[DEBUG] set_system_instructions: Found Save button")
    # breakpoint()  # DEBUG: Before clicking Save
        save_btn.click()
        print("Clicked Save changes")
        print(f"[DEBUG] set_system_instructions: Save clicked")
        time.sleep(2)
        
        # Step 5: Close the panels using Escape key (most reliable)
        print("Closing panels with Escape...")
        print(f"[DEBUG] set_system_instructions: Step 5 - Pressing Escape keys")
    # breakpoint()  # DEBUG: Before Escape keys
        pyautogui.press('escape')
        print(f"[DEBUG] set_system_instructions: Escape 1 pressed")
        time.sleep(0.5)
        pyautogui.press('escape')
        print(f"[DEBUG] set_system_instructions: Escape 2 pressed")
        time.sleep(0.5)
        pyautogui.press('escape')
        print(f"[DEBUG] set_system_instructions: Escape 3 pressed")
        time.sleep(1)
        
        print("System instructions saved!")
        print(f"[DEBUG] set_system_instructions: SUCCESS")
    # breakpoint()  # DEBUG: Success
        return True
        
    except Exception as e:
        print(f"System instructions error: {e}")
        print(f"[DEBUG] set_system_instructions: EXCEPTION: {e}")
    # breakpoint()  # DEBUG: Exception
        # Try to close any open dialogs
        try:
            pyautogui.press('escape')
        except:
            pass
        return False
    finally:
        print(f"[DEBUG] set_system_instructions: Resuming tab monitor")
        resume_monitor()


def save_app(driver, app_name):
    """Save the app with a specific name"""
    # breakpoint()  # DEBUG: Save app workflow
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
    # breakpoint()  # DEBUG: Capturing app URL
    time.sleep(2)
    url = driver.current_url
    print(f"App URL: {url}")
    return url


def save_agent_url(agent_id, url, filename="agents.json"):
    """Save the agent URL to a JSON file"""
    # breakpoint()  # DEBUG: Saving agent URL to JSON
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
    # breakpoint()  # DEBUG: Chat message send workflow start
    print(f"[DEBUG] send_chat_message: ========== STARTING ==========")
    print(f"[DEBUG] send_chat_message: Message length: {len(message)} chars")
    wait = WebDriverWait(driver, 20)  # Increased timeout
    print(f"[DEBUG] send_chat_message: Pausing tab monitor")
    pause_monitor()
    
    try:
        print(f"[send_chat_message] Starting...")
        print(f"[send_chat_message] Current URL: {driver.current_url}")
        print(f"[send_chat_message] Current title: {driver.title}")
        print(f"[send_chat_message] Message preview: {message[:50]}...")
        
        # Step 1: Ensure browser window is focused
        print(f"[DEBUG] send_chat_message: Step 1 - Focusing browser window")
    # breakpoint()  # DEBUG: Before focusing window
        driver.switch_to.window(driver.current_window_handle)
        print(f"[DEBUG] send_chat_message: Switched to current window handle")
        driver.execute_script("window.focus();")
        print(f"[DEBUG] send_chat_message: Executed window.focus()")
        time.sleep(0.5)
        
        # Step 2: Wait for page to be ready (check for chat container)
        print(f"[DEBUG] send_chat_message: Step 2 - Finding chat container")
    # breakpoint()  # DEBUG: Before finding chat container
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.input-container, .chat-input, ms-autosize-textarea")
            ))
            print("[send_chat_message] Chat container found")
            print(f"[DEBUG] send_chat_message: Chat container located")
        except:
            print("[send_chat_message] WARNING: Chat container not found, proceeding anyway")
            print(f"[DEBUG] send_chat_message: WARNING - No chat container")
        
        # Step 3: Find the chatbox with multiple fallback selectors
        print(f"[DEBUG] send_chat_message: Step 3 - Finding chatbox textarea")
    # breakpoint()  # DEBUG: Before finding chatbox
        chatbox = None
        selectors = [
            "div.input-container textarea",
            "ms-autosize-textarea textarea",
            "textarea[placeholder*='message' i]",
            "textarea[placeholder*='type' i]",
            ".chat-input textarea",
            "div.input-area textarea",
            "textarea:not([readonly])"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"[send_chat_message] Selector '{selector}' → {len(elements)} element(s)")
                print(f"[DEBUG] send_chat_message: Trying selector: {selector} -> {len(elements)} found")
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        chatbox = el
                        print(f"[send_chat_message] ✓ Using: {selector}")
                        print(f"[DEBUG] send_chat_message: ✓ Using this element")
    # breakpoint()  # DEBUG: Found chatbox
                        break
                if chatbox:
                    break
            except Exception as e:
                print(f"[DEBUG] send_chat_message: Selector error: {e}")
                continue
        
        if not chatbox:
            print("[send_chat_message] ERROR: Chatbox not found!")
            print(f"[DEBUG] send_chat_message: FAILED - No chatbox found")
    # breakpoint()  # DEBUG: Chatbox not found
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            print(f"[send_chat_message] Found {len(textareas)} textarea(s) on page")
            for i, ta in enumerate(textareas):
                try:
                    print(f"  [{i}] displayed={ta.is_displayed()}, enabled={ta.is_enabled()}, class={ta.get_attribute('class')}")
                except:
                    pass
            return False
        
        # Step 4: Scroll into view and ensure visibility
        driver.execute_script("""
            arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});
        """, chatbox)
        time.sleep(0.3)
        
        # Step 5: Focus with multiple methods
        driver.execute_script("arguments[0].focus();", chatbox)
        time.sleep(0.2)
        
        try:
            chatbox.click()
        except:
            driver.execute_script("arguments[0].click();", chatbox)
        time.sleep(0.3)
        
        # Step 6: Clear and type message
        chatbox.clear()
        time.sleep(0.2)
        
        # Use JavaScript to set value directly - avoids pyautogui OS focus issues
        # pyautogui types to whatever window has OS focus, not necessarily the browser!
        try:
            # Set value directly via JavaScript
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, chatbox, message)
            print("[send_chat_message] Set message via JavaScript")
        except Exception as js_err:
            print(f"[send_chat_message] JS setValue failed: {js_err}, trying send_keys")
            chatbox.send_keys(message)
            print("[send_chat_message] Typed message via send_keys")
        
        time.sleep(1)
        
        # Step 7: Find and click send button
        send_btn = None
        send_selectors = [
            "button.send-button:not([disabled])",
            "button.send-button",
            "button[aria-label*='Send' i]",
            "button[data-test-id='send-button']",
            ".send-button:not([disabled])",
        ]
        
        for selector in send_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        disabled = el.get_attribute("disabled")
                        classes = el.get_attribute("class") or ""
                        if not disabled and "disabled" not in classes:
                            send_btn = el
                            print(f"[send_chat_message] ✓ Send button: {selector}")
                            break
                if send_btn:
                    break
            except:
                continue
        
        if not send_btn:
            print("[send_chat_message] Send button not found, trying Enter key")
            chatbox.send_keys("\n")
            time.sleep(2)
            print("[send_chat_message] Sent via Enter key")
            return True
        
        # Wait a moment for button to become clickable
        time.sleep(0.5)
        
        # Click with JavaScript to bypass any overlays
        driver.execute_script("arguments[0].click();", send_btn)
        print("[send_chat_message] ✓ Clicked Send button")
        
        # P9 Phase 4: Wait for AI to finish processing (event-driven via WebDriverWait)
        response_text = None
        try:
            print("[send_chat_message] Waiting for AI to finish (event-driven)...")
            
            # Custom expected condition: AI finished when no running/thinking/cancel indicators
            def ai_finished(driver):
                # Check if still processing
                running = driver.find_elements(By.CSS_SELECTOR, "button.send-button.running")
                thinking = driver.find_elements(By.CSS_SELECTOR, "ms-thinking-indicator")
                cancel = driver.find_elements(By.CSS_SELECTOR, "button.send-button[aria-label='Cancel']")
                
                if running or thinking or cancel:
                    return False  # Still processing
                
                # Also check for Checkpoint indicator (AI finished writing)
                checkpoint = driver.find_elements(By.XPATH, "//div[contains(text(), 'Checkpoint')]")
                if checkpoint:
                    print("[send_chat_message] ✓ Checkpoint detected")
                    return True
                    
                return True  # No processing indicators
            
            # Wait up to 120 seconds for AI to finish (event-driven, not polling)
            wait = WebDriverWait(driver, 120, poll_frequency=1)
            try:
                wait.until(ai_finished)
                print("[send_chat_message] ✓ AI finished processing")
            except TimeoutException:
                print("[send_chat_message] Timeout waiting for AI, proceeding anyway...")
            
            # Brief pause to ensure output.md is fully written
            time.sleep(2)
            
            # P9 Phase 5: Read response from output.md via Monaco editor
            print("[send_chat_message] Looking for output.md in file tree...")
            
            # Step 1: Find and click output.md in file tree
            # The file tree uses: mat-tree-node with span.node-name containing filename
            output_md_clicked = False
            try:
                # Find all file nodes in the tree
                file_nodes = driver.find_elements(By.CSS_SELECTOR, "mat-tree-node span.node-name")
                for node in file_nodes:
                    if node.text.strip().lower() == "output.md":
                        # Click the parent mat-tree-node to select the file
                        parent_node = node.find_element(By.XPATH, "./ancestor::mat-tree-node")
                        driver.execute_script("arguments[0].click();", parent_node)
                        output_md_clicked = True
                        print("[send_chat_message] ✓ Clicked output.md in file tree")
                        break
                
                if not output_md_clicked:
                    print("[send_chat_message] output.md not found in file tree")
            except Exception as e:
                print(f"[send_chat_message] Error clicking output.md: {e}")
            
            if output_md_clicked:
                # Step 2: Wait for Monaco editor to load output.md
                time.sleep(1.5)  # Wait for editor to switch
                
                # Verify editor shows output.md (check data-uri attribute)
                try:
                    editor = driver.find_element(By.CSS_SELECTOR, "div.monaco-editor[data-uri*='output.md']")
                    print("[send_chat_message] ✓ Monaco editor loaded output.md")
                except:
                    # Editor might just take a moment
                    time.sleep(1)
                    print("[send_chat_message] Waiting for editor to load output.md...")
                
                # Step 3: Read content from Monaco editor view-lines
                try:
                    # Debug: Try multiple selectors
                    view_lines = driver.find_elements(By.CSS_SELECTOR, "div.view-lines.monaco-mouse-cursor-text div.view-line")
                    print(f"[send_chat_message] DEBUG: Found {len(view_lines)} view-line elements")
                    
                    if not view_lines:
                        # Fallback: try without the mouse-cursor-text class
                        view_lines = driver.find_elements(By.CSS_SELECTOR, "div.view-lines div.view-line")
                        print(f"[send_chat_message] DEBUG: Fallback found {len(view_lines)} view-line elements")
                    
                    lines = []
                    for line in view_lines:
                        # Each line has span elements with class mtk1, mtk8, etc.
                        line_text = line.text.strip()
                        if line_text:
                            lines.append(line_text)
                    
                    print(f"[send_chat_message] DEBUG: Extracted {len(lines)} non-empty lines")
                    
                    if lines:
                        response_text = "\n".join(lines)
                        print(f"[send_chat_message] ✓ Read {len(lines)} lines from output.md")
                        logger.debug("CHAT", f"Response captured ({len(response_text)} chars)")
                        
                        # P9: After first response, save URL and mark agent active
                        # Find which agent this tab belongs to
                        current_handle = driver.current_window_handle
                        print(f"[send_chat_message] DEBUG: Looking for handle {current_handle[:20]}... in agent_handles")
                        print(f"[send_chat_message] DEBUG: agent_handles = {list(agent_handles.keys())}")
                        
                        for aid, handle in agent_handles.items():
                            if handle == current_handle:
                                print(f"[send_chat_message] DEBUG: Found matching agent: {aid}")
                                # Check if agent is still in "spawning" status
                                agent_data = db_get_agent(aid)
                                print(f"[send_chat_message] DEBUG: agent_data status = {agent_data.get('status') if agent_data else 'None'}")
                                
                                if agent_data and agent_data.get("status") == "spawning":
                                    # First response received! Save URL and mark active
                                    current_url = driver.current_url
                                    db_upsert_agent(aid, status="active", drive_url=current_url)
                                    logger.info("AGENT", f"First response received, agent now active", {
                                        "agent_id": aid,
                                        "url": current_url[:50]
                                    })
                                    print(f"[send_chat_message] ✓ Agent {aid} marked ACTIVE, URL saved")
                                break
                except Exception as e:
                    print(f"[send_chat_message] Error reading Monaco editor: {e}")
                     
        except Exception as e:
            logger.warning("CHAT", f"Response capture failed: {e}")
        
        print(f"[send_chat_message] ✓ Message sent successfully!")
        return response_text if response_text else True
        
    except Exception as e:
        print(f"[send_chat_message] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        resume_monitor()


def select_model(driver, model_name="Gemini 3 Pro Preview", skip_close=False):
    """Select the AI model from Advanced settings dropdown
    
    Args:
        skip_close: If True, don't close the settings panel (for when set_system_instructions follows)
    """
    # breakpoint()  # DEBUG: Model selection workflow
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
        
        # Step 4: Close the panel with Escape (unless skip_close is True)
        if not skip_close:
            print("Closing Advanced settings...")
            pyautogui.press('escape')
            time.sleep(0.5)
            pyautogui.press('escape')
            time.sleep(1)
        else:
            print("Keeping settings panel open for next step...")
        
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
    """Spawn a single agent: create zip, upload, configure, save
    
    P8 Flow:
    - Phase 0: Check if agent has URL in DB
    - Phase R: Reactivate (if URL exists) - fast path
    - Phase 1-8: Full spawn (if no URL)
    """
    # breakpoint()  # DEBUG: Agent spawn workflow start
    global agent_handles
    
    logger.info("AGENT", f"Spawn requested: {agent_id}")
    
    # ==========================================================================
    # P8 Phase 0: Check for Reactivation
    # ==========================================================================
    existing_agent = db_get_agent(agent_id)
    
    if existing_agent and existing_agent.get("drive_url"):
        # =======================================================================
        # P8 Phase R: Reactivate (fast path)
        # =======================================================================
        logger.info("AGENT", f"Reactivating {agent_id} from saved URL")
        saved_url = existing_agent["drive_url"]
        print(f"[REACTIVATE] Saved URL from DB: {saved_url}")
        
        try:
            # Get current handles to determine if first agent
            handles_before = driver.window_handles
            print(f"[REACTIVATE] Current tabs: {len(handles_before)}")
            
            # Check if we already have agent tabs (besides the base AI Studio tab)
            is_first_agent = len(agent_handles) == 0
            
            if is_first_agent:
                # First agent - navigate in current tab (no new tab needed)
                print(f"[REACTIVATE] First agent - using current tab")
                new_handle = driver.current_window_handle
                driver.get(saved_url)
            else:
                # Not first agent - open new tab then navigate
                print(f"[REACTIVATE] Additional agent - opening new tab")
                driver.execute_script("window.open('');")
                time.sleep(0.5)
                handles_after = driver.window_handles
                new_handle = handles_after[-1]
                driver.switch_to.window(new_handle)
                driver.get(saved_url)
            print(f"[REACTIVATE] driver.get() called")
            
            # Wait for page to load (use WebDriverWait instead of sleep)
            wait = WebDriverWait(driver, 10)
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                logger.warning("AGENT", "Page load timeout during reactivation")
            
            # Check if redirected to login
            if "accounts.google.com" in driver.current_url:
                logger.warning("AGENT", "Login required during reactivation, falling back to full spawn")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                # Fall through to full spawn
            else:
                # Verify page loaded correctly (give it a moment for title to update)
                time.sleep(2)
                title = driver.title
                current_url = driver.current_url
                
                # Check if we're on AI Studio (not an error page)
                if "aistudio.google.com" in current_url:
                    # Store handle in memory
                    agent_handles[agent_id] = new_handle
                    
                    # Update status in DB
                    db_upsert_agent(agent_id, status="active")
                    
                    logger.info("AGENT", f"Reactivated {agent_id} successfully", {
                        "title": title[:50] if title else "N/A",
                        "url": current_url[:50]
                    })
                    return True
                else:
                    logger.warning("AGENT", f"Reactivation landed on unexpected URL", {"url": current_url})
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    # Fall through to full spawn
            
        except Exception as e:
            logger.error("AGENT", f"Reactivation failed, falling back to full spawn", {"error": str(e)})
    
    # ==========================================================================
    # P8 Phase 1: Full Spawn (no saved URL)
    # ==========================================================================
    logger.info("AGENT", f"Full spawn starting for {agent_id}")
    
    # Get agent skill info
    skill = get_agent_skill(agent_id)
    if not skill:
        logger.error("AGENT", f"Failed to get skill for {agent_id}")
        return False
    
    # Create agent zip
    zip_path = create_agent_zip(agent_id)
    if not zip_path:
        logger.error("AGENT", f"Failed to create zip for {agent_id}")
        return False
    
    # ==========================================================================
    # P11 Fix 1: Open new tab if there are already active agents
    # This prevents overwriting an existing agent's tab
    # ==========================================================================
    if agent_handles:
        print(f"[spawn_agent] P11: {len(agent_handles)} agents already active, opening new tab")
        driver.execute_script("window.open('');")
        time.sleep(0.5)
        # Switch to the new tab (last one)
        new_handle = driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        print(f"[spawn_agent] P11: Switched to new tab")
    else:
        print(f"[spawn_agent] P11: First agent, using current tab")
    
    # Navigate to new app page
    url = "https://aistudio.google.com/apps/bundled/blank?showAssistant=true&showCode=true"
    print(f"Navigating to: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Select Gemini 3 Pro Preview model (keep panel open for system instructions)
    select_model(driver, "Gemini 3 Pro Preview", skip_close=True)
    
    # Set system instructions from SKILL.md (panel already open from select_model)
    # This closes the panel when done
    set_system_instructions(driver, skill["skill_content"], skip_open=True)
    
    # Now upload files (panel is closed)
    # Upload the agent zip
    if not upload_zip(driver, zip_path):
        print(f"Failed to upload zip for {agent_id}")
        return False
    
    # Upload core.txt (the project documentation these agents work on)
    core_txt = os.path.abspath("core.txt")
    if os.path.exists(core_txt):
        print(f"Uploading project: core.txt")
        upload_files(driver, ["core.txt"])
    else:
        print(f"core.txt not found, skipping project upload")
    
    # Save app with agent name
    app_name = f"AGENT: {agent_id}"
    save_app(driver, app_name)
    
    # Get app URL (save it for later, after first response)
    app_url = get_app_url(driver)
    
    # P5: Save to SQLite database - but DON'T save drive_url yet
    # URL will be saved after first AI response confirms agent is working
    db_upsert_agent(
        agent_id=agent_id,
        name=skill["name"],
        description=skill["description"],
        status="spawning"  # Not "active" until first response
        # drive_url=app_url  # Saved after first response
    )
    logger.info("AGENT", "Agent saved to database (awaiting first response)", {"agent_id": agent_id, "url": app_url})
    
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
    
    # Store window handle in memory BEFORE sending init message
    # This is needed so send_chat_message can find this agent and update status
    agent_handles[agent_id] = driver.current_window_handle
    logger.debug("AGENT", "Tab handle stored", {"agent_id": agent_id, "handle": agent_handles[agent_id]})
    
    send_chat_message(driver, init_message)
    
    logger.info("AGENT", "Agent spawned successfully", {"agent_id": agent_id})
    return True


def capture_agent_handles(driver):
    """Scan all open tabs and capture handles for AGENT: tabs"""
    # breakpoint()  # DEBUG: Scanning tabs for agent handles
    global agent_handles
    
    try:
        original_handle = driver.current_window_handle
    except:
        original_handle = None
    
    handles = driver.window_handles
    print(f"[capture_agent_handles] Scanning {len(handles)} tabs...")
    
    # Clear old handles that are no longer valid
    agent_handles = {k: v for k, v in agent_handles.items() if v in handles}
    
    for handle in handles:
        try:
            driver.switch_to.window(handle)
            time.sleep(0.5)  # Wait for title to load
            title = driver.title
            url = driver.current_url
            
            print(f"[capture_agent_handles] Tab: {handle[:20]}... | Title: {title[:40]}")
            
            # Look for "AGENT: XXX" in title
            if "AGENT:" in title:
                parts = title.split("AGENT:")
                if len(parts) > 1:
                    agent_id = parts[1].split("|")[0].strip()
                    if agent_id:
                        agent_handles[agent_id] = handle
                        print(f"[capture_agent_handles] ✓ Found {agent_id} → {handle}")
        except Exception as e:
            print(f"[capture_agent_handles] Error on handle {handle}: {e}")
    
    # Return to original tab
    if original_handle and original_handle in handles:
        try:
            driver.switch_to.window(original_handle)
        except:
            pass
    elif handles:
        try:
            driver.switch_to.window(handles[0])
        except:
            pass
    
    print(f"[capture_agent_handles] Result: {list(agent_handles.keys())}")
    return agent_handles


def login_to_google(driver, wait):
    """P4 Phase 9: Login to Google if needed"""
    # breakpoint()  # DEBUG: Google login flow
    email = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")

    if not email or not password:
        logger.warning("LOGIN", "No credentials in .env, manual login required")
        return

    pause_monitor()

    try:
        logger.info("LOGIN", "Entering email...")
        email_field = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//input[@type="email"]')
        ))
        email_field.clear()
        email_field.send_keys(email)
        email_field.send_keys("\n")
        logger.debug("LOGIN", "Email entered")
        
        time.sleep(3)

        logger.info("LOGIN", "Entering password...")
        password_field = wait.until(EC.visibility_of_element_located(
            (By.XPATH, '//input[@type="password"]')
        ))
        password_field.clear()
        password_field.send_keys(password)
        password_field.send_keys("\n")
        logger.debug("LOGIN", "Password entered")
        
        logger.info("LOGIN", "Waiting for login to complete...")
        wait.until(lambda d: "accounts.google.com" not in d.current_url)
        logger.info("LOGIN", "Login successful!")

    except Exception as e:
        logger.error("LOGIN", "Auto-login failed, manual login required", {"error": str(e)})
        try:
            WebDriverWait(driver, 120).until(
                lambda d: "aistudio.google.com" in d.current_url
            )
            logger.info("LOGIN", "Manual login completed")
        except:
            logger.warning("LOGIN", "Login timeout, continuing anyway")
    finally:
        resume_monitor()



def main():
    """Original standalone main - spawns one agent then waits"""
    # breakpoint()  # DEBUG: Standalone main entry
    extension_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extension"))
    profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chrome_profile"))
    
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
        
        # Standalone mode: spawn one agent
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


# ============================================
# FLASK API SERVER
# ============================================

app = Flask(__name__)
CORS(app)

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        "status": "online" if driver_ref else "offline",
        "driver_initialized": driver_ref is not None
    })

@app.route('/api/agents', methods=['GET'])
def api_agents():
    """Return only agents that have active window handles (from memory + DB info)"""
    global agent_handles
    
    active = {}
    
    # For each agent with a window handle, get its info from database
    for agent_id in agent_handles.keys():
        agent_data = db_get_agent(agent_id)
        if agent_data:
            active[agent_id] = {
                "id": agent_id,
                "name": agent_data.get("name", agent_id),
                "description": agent_data.get("description", ""),
                "url": agent_data.get("drive_url", ""),
                "status": "active",
                "created_at": agent_data.get("created_at", "")
            }
        else:
            # Agent in handles but not in DB - use minimal info
            active[agent_id] = {
                "id": agent_id,
                "name": agent_id,
                "description": "",
                "url": "",
                "status": "active",
                "created_at": ""
            }
    
    return jsonify(active)

@app.route('/api/roster', methods=['GET'])
def api_roster():
    roster = {}
    if os.path.exists(SKILLS_PATH):
        for agent_id in os.listdir(SKILLS_PATH):
            skill = get_agent_skill(agent_id)
            if skill:
                category = agent_id.split("-")[0] if "-" in agent_id else "OTHER"
                if category not in roster:
                    roster[category] = []
                roster[category].append({
                    "id": agent_id,
                    "name": skill["name"],
                    "description": skill["description"]
                })
    return jsonify(roster)

@app.route('/api/spawn', methods=['POST'])
def api_spawn():
    # breakpoint()  # DEBUG: API spawn endpoint hit
    global driver_ref
    
    # P12: Ensure browser is running, recover if dead
    driver_ref = ensure_browser()
    if not driver_ref:
        return jsonify({"error": "Browser not initialized and recovery failed"}), 503
    
    data = request.json
    agent_id = data.get('agent_id')
    if not agent_id:
        return jsonify({"error": "Missing agent_id"}), 400
    
    try:
        def do_spawn():
            spawn_agent(driver_ref, agent_id)
        
        t = threading.Thread(target=do_spawn, daemon=True)
        t.start()
        
        return jsonify({"status": "spawning", "agent_id": agent_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/deactivate', methods=['POST'])
def api_deactivate():
    """Deactivate an agent: close its tab and mark as inactive"""
    global driver_ref, agent_handles
    
    print(f"[api_deactivate] ═══════════════════════════════════════")
    
    if not driver_ref:
        print("[api_deactivate] ERROR: Browser not initialized")
        return jsonify({"error": "Browser not initialized"}), 503
    
    data = request.json
    agent_id = data.get('agent_id')
    
    if not agent_id:
        print("[api_deactivate] ERROR: Missing agent_id")
        return jsonify({"error": "Missing agent_id"}), 400
    
    print(f"[api_deactivate] Deactivating: {agent_id}")
    logger.info("AGENT", f"Deactivating agent: {agent_id}")
    
    # Pause tab monitor during deactivation
    pause_monitor()
    
    try:
        # Find the agent's window handle
        handle = agent_handles.get(agent_id)
        print(f"[api_deactivate] Handle in memory: {handle}")
        print(f"[api_deactivate] All handles in memory: {list(agent_handles.keys())}")
        
        if handle:
            try:
                # Check if handle is still valid
                current_handles = driver_ref.window_handles
                print(f"[api_deactivate] Browser handles: {len(current_handles)}")
                
                if handle in current_handles:
                    # Switch to the tab and close it
                    print(f"[api_deactivate] Switching to tab...")
                    driver_ref.switch_to.window(handle)
                    print(f"[api_deactivate] Closing tab...")
                    driver_ref.close()
                    
                    # Switch back to another tab
                    remaining_handles = driver_ref.window_handles
                    if remaining_handles:
                        driver_ref.switch_to.window(remaining_handles[0])
                        print(f"[api_deactivate] Switched to first remaining tab")
                    
                    logger.info("AGENT", f"Closed tab for {agent_id}")
                    print(f"[api_deactivate] ✓ Tab closed")
                else:
                    print(f"[api_deactivate] Handle no longer valid (tab already closed?)")
                
            except InvalidSessionIdException:
                # P12 Fix: Browser session is dead - mark driver_ref as stale
                print(f"[api_deactivate] P12: Browser session dead, marking driver_ref as None")
                driver_ref = None
                agent_handles.clear()  # All handles are invalid now
            except Exception as tab_error:
                print(f"[api_deactivate] Tab close error (non-fatal): {tab_error}")
                # Continue even if tab close fails
            
            # Remove from memory
            del agent_handles[agent_id]
            print(f"[api_deactivate] ✓ Removed from memory")
        else:
            print(f"[api_deactivate] Agent not in memory (already deactivated?)")
        
        # Update database status (always do this)
        db_upsert_agent(agent_id, status="inactive")
        print(f"[api_deactivate] ✓ DB updated to 'inactive'")
        logger.info("AGENT", f"Agent marked inactive: {agent_id}")
        
        return jsonify({"status": "deactivated", "agent_id": agent_id})
        
    except Exception as e:
        import traceback
        print(f"[api_deactivate] ERROR: {e}")
        traceback.print_exc()
        logger.error("AGENT", f"Deactivation failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        resume_monitor()

@app.route('/api/chat', methods=['POST'])
def api_chat():
    # breakpoint()  # DEBUG: API chat endpoint hit
    global driver_ref, agent_handles
    if not driver_ref:
        return jsonify({"error": "Browser not initialized"}), 503
    
    data = request.json
    message = data.get('message')
    agent_id = data.get('agent_id')
    
    if not message:
        return jsonify({"error": "Missing message"}), 400
    
    try:
        # Get current valid handles from browser
        current_handles = driver_ref.window_handles
        print(f"[api_chat] ═══════════════════════════════════════")
        print(f"[api_chat] Browser tabs open: {len(current_handles)}")
        print(f"[api_chat] Stored agent handles: {list(agent_handles.keys())}")
        
        if agent_id:
            if agent_id not in agent_handles:
                print(f"[api_chat] Agent {agent_id} not in stored handles, rescanning...")
                capture_agent_handles(driver_ref)
            
            if agent_id not in agent_handles:
                return jsonify({"error": f"Agent {agent_id} not found in any tab"}), 404
            
            handle = agent_handles[agent_id]
            print(f"[api_chat] Target handle for {agent_id}: {handle}")
            
            # Validate handle is still valid
            if handle not in current_handles:
                print(f"[api_chat] Handle {handle} is STALE! Rescanning...")
                capture_agent_handles(driver_ref)
                
                if agent_id not in agent_handles:
                    return jsonify({"error": f"Agent {agent_id} tab was closed"}), 404
                    
                handle = agent_handles[agent_id]
                print(f"[api_chat] New handle after rescan: {handle}")
            
            # Switch to the agent's tab
            print(f"[api_chat] Switching to tab: {handle}")
            driver_ref.switch_to.window(handle)
            
            # Wait for switch and verify
            time.sleep(1)
            actual_handle = driver_ref.current_window_handle
            if actual_handle != handle:
                print(f"[api_chat] WARNING: Switch may have failed. Current: {actual_handle}")
            
            # Additional wait for page to stabilize
            time.sleep(1.5)
            
            print(f"[api_chat] Now on tab: {driver_ref.title}")
            print(f"[api_chat] URL: {driver_ref.current_url}")
            
            # Send the message and capture response
            result = send_chat_message(driver_ref, message)
            
            # P9: Return response if captured
            if result:
                if isinstance(result, str):
                    return jsonify({
                        "status": "sent",
                        "agent_id": agent_id,
                        "response": result
                    })
                else:
                    return jsonify({
                        "status": "sent",
                        "agent_id": agent_id
                    })
            else:
                return jsonify({"error": "Failed to send message - check backend logs"}), 500
                
        else:
            # =====================================================================
            # P10: BROADCAST MODE - Send to ALL active agents
            # =====================================================================
            if not agent_handles:
                return jsonify({"error": "No active agents to broadcast to"}), 400
            
            print(f"[api_chat] ═══════════════════════════════════════")
            print(f"[api_chat] BROADCAST MODE: Sending to {len(agent_handles)} agents")
            print(f"[api_chat] Agents: {list(agent_handles.keys())}")
            
            results = {}
            success_count = 0
            error_count = 0
            
            for aid in list(agent_handles.keys()):  # Use list() to avoid dict modification during iteration
                print(f"[api_chat] ───────────────────────────────────────")
                print(f"[api_chat] Broadcasting to: {aid}")
                
                try:
                    handle = agent_handles[aid]
                    
                    # Validate handle is still valid
                    if handle not in current_handles:
                        print(f"[api_chat] Handle for {aid} is stale, skipping")
                        results[aid] = {"success": False, "error": "Tab was closed"}
                        error_count += 1
                        continue
                    
                    # Switch to agent's tab
                    driver_ref.switch_to.window(handle)
                    time.sleep(1)
                    
                    print(f"[api_chat] Switched to: {driver_ref.title}")
                    
                    # Send message and capture response
                    response = send_chat_message(driver_ref, message)
                    
                    if response:
                        if isinstance(response, str):
                            results[aid] = {"success": True, "response": response}
                        else:
                            results[aid] = {"success": True}
                        success_count += 1
                        print(f"[api_chat] ✓ {aid}: Message sent")
                    else:
                        results[aid] = {"success": False, "error": "Failed to send"}
                        error_count += 1
                        print(f"[api_chat] ✗ {aid}: Send failed")
                        
                except Exception as e:
                    print(f"[api_chat] ✗ {aid}: Exception - {e}")
                    results[aid] = {"success": False, "error": str(e)}
                    error_count += 1
            
            print(f"[api_chat] ═══════════════════════════════════════")
            print(f"[api_chat] BROADCAST COMPLETE: {success_count} success, {error_count} failed")
            
            return jsonify({
                "broadcast": True,
                "total": len(agent_handles),
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            })
            
    except Exception as e:
        print(f"[api_chat] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def run_flask():
    # Quiet down Werkzeug logging - hide /api/status spam
    import logging
    werkzeug_log = logging.getLogger('werkzeug')
    
    class StatusFilter(logging.Filter):
        def filter(self, record):
            # Hide polling requests from terminal
            msg = record.getMessage()
            if '/api/status' in msg or '/api/agents' in msg:
                return False
            return True
    
    werkzeug_log.addFilter(StatusFilter())
    
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def main_with_api():
    """Main function that runs browser + Flask API server"""
    # breakpoint()  # DEBUG: Application startup
    global driver_ref
    
    # ==========================================================================
    # P2 Phase 3: Chrome Setup
    # ==========================================================================
    extension_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extension"))
    profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chrome_profile"))
    
    logger.debug("CHROME", "Extension path resolved", {"path": extension_path})
    logger.debug("CHROME", "Profile path resolved", {"path": profile_path})
    
    # Check if profile exists (determines if we have saved session)
    if os.path.exists(profile_path):
        logger.info("PROFILE", "Loading saved session", {"path": profile_path})
    else:
        logger.info("PROFILE", "Fresh Chrome instance (no saved profile)", {"path": profile_path})
    
    options = uc.ChromeOptions()
    options.add_argument(f"--load-extension={extension_path}")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    logger.info("CHROME", "Chrome options configured")
    
    # ==========================================================================
    # P2 Phase 4: Chrome Launch
    # ==========================================================================
    logger.info("CHROME", "Launching Chrome...")
    
    try:
        driver = uc.Chrome(options=options)
        logger.info("CHROME", "Chrome launched successfully")
    except Exception as e:
        logger.error("CHROME", "Chrome launch failed", {"error": str(e)})
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    driver_ref = driver
    wait = WebDriverWait(driver, 5)  # P2: 5 second timeout
    logger.info("CHROME", "Driver ready", {"timeout": 5})
    
    try:
        # ======================================================================
        # P3 Phase 5: Extension Load
        # ======================================================================
        logger.info("CHROME", "Waiting for extension to load...")
        # Extension loads automatically with Chrome - no sleep needed
        logger.info("CHROME", "Extension loaded")
        
        # ======================================================================
        # P3 Phase 6: Navigate to AI Studio
        # ======================================================================
        url = "https://aistudio.google.com/apps/bundled/blank?showAssistant=true&showCode=true"
        logger.info("NAVIGATION", "Navigating to AI Studio", {"url": url})
        driver.get(url)
        logger.debug("NAVIGATION", "Navigation started")
        
        # Wait for page element instead of time.sleep(3)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("NAVIGATION", "Page loaded")
        except Exception as e:
            logger.warning("NAVIGATION", "Page load wait timeout, continuing anyway", {"error": str(e)})
        
        # ======================================================================
        # P4 Phase 7: Dismiss Popups
        # ======================================================================
        def dismiss_popups():
            """Dismiss cookie consent and ToS banners if present"""
            try:
                # Cookie consent - look for Disagree/Reject button
                for selector in [
                    "//button[contains(text(), 'Disagree')]",
                    "//button[contains(text(), 'Reject')]",
                    "//button[contains(@aria-label, 'Disagree')]",
                ]:
                    try:
                        btns = driver.find_elements(By.XPATH, selector)
                        for btn in btns:
                            if btn.is_displayed():
                                btn.click()
                                logger.info("POPUP", "Cookie consent dismissed")
                                time.sleep(0.5)
                                break
                    except:
                        pass
                
                # ToS banner - look for Dismiss button
                for selector in [
                    "//button[contains(text(), 'Dismiss')]",
                    "//button[contains(text(), 'Got it')]",
                    "//button[contains(text(), 'OK')]",
                ]:
                    try:
                        btns = driver.find_elements(By.XPATH, selector)
                        for btn in btns:
                            if btn.is_displayed():
                                btn.click()
                                logger.info("POPUP", "ToS/notice dismissed")
                                time.sleep(0.5)
                                break
                    except:
                        pass
            except Exception as e:
                logger.debug("POPUP", "No popups to dismiss or error", {"error": str(e)})
        
        dismiss_popups()
        
        # ======================================================================
        # P4 Phase 8: Tab Monitor (First Time Only)
        # ======================================================================
        # profile_exists is determined by whether chrome_profile directory existed
        profile_existed = os.path.exists(profile_path) and len(os.listdir(profile_path)) > 0
        
        if not profile_existed:
            logger.info("TAB", "Starting tab monitor (first-time setup)")
            start_tab_monitor(driver)
            logger.debug("TAB", "Tab monitor running")
        else:
            logger.info("TAB", "Skipping tab monitor (profile exists)")
        
        # ======================================================================
        # P4 Phase 9: Login Check
        # ======================================================================
        logger.info("LOGIN", "Checking authentication status...")
        if "accounts.google.com" in driver.current_url:
            logger.info("LOGIN", "Login required - redirected to Google")
            login_to_google(driver, wait)
        else:
            logger.info("LOGIN", "Already authenticated")
        
        # Scan existing tabs for agent handles
        capture_agent_handles(driver)
        
        # Start Flask API in background
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("FLASK", "API server started on http://127.0.0.1:5000")
        # ======================================================================
        # P5 Phase 12: Ready / Keep Alive
        # ======================================================================
        logger.info("READY", "Browser + API ready")
        print("\nBrowser + API ready. Use frontend to control agents.")
        print("Press Ctrl+C to exit.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("SHUTDOWN", "User requested exit (Ctrl+C)")
    except Exception as e:
        logger.error("SHUTDOWN", "Unexpected error", {"error": str(e)})
        import traceback
        traceback.print_exc()
    finally:
        logger.info("SHUTDOWN", "Cleaning up...")
        stop_all()
        try:
            driver.quit()
            logger.info("SHUTDOWN", "Chrome closed")
        except:
            pass
        logger.info("SHUTDOWN", "Goodbye!")


if __name__ == "__main__":
    main_with_api()
