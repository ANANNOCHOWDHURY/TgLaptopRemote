"""
Direct Telegram <-> Windows Laptop Control (BotFather-style bottom keyboard)
-------------------------------------------------------------------------------
No VPS, no n8n, no Cloudflare Worker. This single script runs on your
laptop and talks directly to Telegram's Bot API using long polling.
Uses a persistent bottom "reply keyboard" (same style as BotFather's
own button grid) instead of inline buttons.

SETUP:
  1. Fill in YOUR INFO in the block right below (BOT_TOKEN, OWNER_CHAT_ID, BOT_PASSWORD).
  2. Just run: python telegram_laptop_bot.py
     (it auto-installs any missing packages the first time it runs)
  3. Send your password to the bot, then send /menu to see the keyboard.

TO RUN HIDDEN / AUTO-START ON BOOT (no terminal window needed):
  See the Task Scheduler steps — set the Action's Program to pythonw.exe
  (not python.exe) and Arguments to this script's full path. pythonw.exe
  runs with no console window at all; logs/errors go to
  %TEMP%\\telegram_bot_log.txt instead of a terminal.
"""


BOT_TOKEN = ""
OWNER_CHAT_ID = ""
BOT_PASSWORD = ""
ANTITHEFT_CONTACT_MSG = (
    "এই ল্যাপটপটি হারিয়ে গেছে।\nফেরত দিতে যোগাযোগ করুন: YOUR_PHONE_NUMBER"
)
ANTITHEFT_PIN = ""


import importlib
import os
import subprocess
import sys
import threading
import time
import traceback
import ctypes


if sys.stdout is None or sys.stderr is None:
    _log_path = os.path.join(os.environ.get("TEMP", "."), "telegram_bot_log.txt")
    _log_file = open(_log_path, "a", buffering=1, encoding="utf-8")
    sys.stdout = _log_file
    sys.stderr = _log_file


_REQUIRED_PACKAGES = {
    "requests": "requests",
    "mss": "mss",
    "win32com.client": "pywin32",
    "pyautogui": "pyautogui",
}


def _ensure_dependencies():
    for module_name, pip_name in _REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            print(f"[setup] Installing missing package: {pip_name} ...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                print(f"[setup] Could not install {pip_name} automatically: {e}")
                print(f"[setup] Try running manually: pip install {pip_name}")


_ensure_dependencies()

import requests


import ctypes as _ctypes

_mutex = _ctypes.windll.kernel32.CreateMutexW(None, False, "TelegramLaptopBot_SingleInstance")
if _ctypes.windll.kernel32.GetLastError() == 183:
    print("[startup] Another instance of this bot is already running. Exiting.")
    sys.exit(0)


UPLOAD_DIR = os.path.expanduser("~\\Downloads\\TelegramBotFiles")
DESKTOP_DIR = os.path.expanduser("~\\Desktop")

if not BOT_TOKEN or not OWNER_CHAT_ID or not BOT_PASSWORD:
    print("[setup] Fill in BOT_TOKEN, OWNER_CHAT_ID and BOT_PASSWORD at the top of this file, then restart.")
    sys.exit(1)


ANTITHEFT_PIN = ANTITHEFT_PIN or BOT_PASSWORD


API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = os.path.join(os.environ.get("TEMP", "."), "telegram_bot_offset.txt")


PENDING = {}


AUTHENTICATED = set()


CURRENT_DIR = {}


NAV_CACHE = {}


RENAME_STATE = {}


MAIN_KEYBOARD = {
    "keyboard": [
        ["📸 Screenshot", "💻 My PC"],
        ["🖥️ Run Command", "📂 Open App"],
        ["🌐 Chrome", "📥 Get File"],
        ["❌ Close App"],
        ["🔒 Lock PC", "📍 Location"],
        ["🚨 Anti-theft Lock", "🔓 Remote Unlock"],
        ["🔌 Shutdown", "🔄 Restart"],
        ["❓ Help"],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

CONFIRM_KEYBOARD = {
    "keyboard": [["✅ Yes, do it", "🚫 Cancel"]],
    "resize_keyboard": True,
}

HELP_TEXT = (
    "নিচের কীবোর্ড থেকে বাটনে চাপ দাও, অথবা এই কমান্ডগুলো টাইপ করো:\n\n"
    "/cmd <powershell command>\n/screenshot\n/ls <path>\n"
    "/open <app>\n/close <app.exe>\n/lock\n/shutdown\n/restart\n"
    "/get <file path>\n/search <query> (ডিফল্ট মোডে)\n/menu — কীবোর্ড আবার দেখাতে\n\n"
    "🌐 Chrome বাটনে চাপ দিলে আগে জিজ্ঞেস করবে Default (সাইন-ইন করা) নাকি "
    "Incognito (সাইন-ইন ছাড়া) দিয়ে চালাবে, তারপর কী লিখবে জিজ্ঞেস করবে। "
    "সেটা লিখে দিলে Chrome খুলে address bar-এ লিখে সাথে সাথে Enter-ও চেপে দেবে "
    "(URL হলে সরাসরি সেই পেজে চলে যাবে, নাহলে Google-এ সার্চ হয়ে যাবে)।\n\n"
    "💻 My PC বাটনে চাপ দিলে আগে সব ড্রাইভ (C:, D: ইত্যাদি) দেখাবে, তারপর "
    "ফোল্ডারে ঢুকতে বাটনে চাপ দাও। ফাইলগুলো শুধু নাম হিসেবে লিস্টে দেখাবে (বাটন না)। "
    "⬅️ Back আর 📥 Download বাটন সবসময় উপরেই থাকবে — Download-এ চাপ দিয়ে ফাইলের "
    "নাম লিখলে (যেমন: png2.png) সেটা সরাসরি তোমাকে পাঠিয়ে দেবে।\n\n"
    "কোনো ফোল্ডারের ভেতরে থাকলে আরও কিছু বাটন দেখবে:\n"
    "📁+ New Folder / 📄+ New File — নতুন ফোল্ডার/ফাইল বানাতে\n"
    "🗑️ Delete — ফাইল/ফোল্ডার ডিলিট করতে (নাম চাইবে)\n"
    "✏️ Rename — নাম পরিবর্তন করতে (আগের নাম, তারপর নতুন নাম চাইবে)\n"
    "⬆️ Upload Here — এই বাটনে চাপ দিয়ে ফাইল পাঠালে সেটা বর্তমান ফোল্ডারেই সেভ হবে\n\n"
    "ফাইল সরাসরি attach করে পাঠালে (কোনো বাটন না চেপে) সেটা Downloads\\TelegramBotFiles-এ সেভ হবে।\n\n"
    "📍 Location — IP-ভিত্তিক আনুমানিক লোকেশন পাঠাবে (Google Maps লিংকসহ)।\n"
    "🚨 Anti-theft Lock — ল্যাপটপে একটা fullscreen lock screen দেখাবে (হারানো/চুরির নোটিশ + "
    "যোগাযোগের নম্বর), PIN দিলেই খুলবে, অথবা এখান থেকেই 🔓 Remote Unlock চেপে দূর থেকেও বন্ধ "
    "করা যাবে। Task Manager দিয়েও বন্ধ করা সম্ভব, তাই এটা 100% নিশ্চয়তা না, একটা deterrent মাত্র।\n\n"
    "লক হলে/আনলক হলে (স্বাভাবিক Windows lock screen দিয়ে) এমনিতেই তোমাকে আলাদা "
    "নোটিফিকেশন পাঠানো হয়।"
)


def get_updates(offset):
    resp = requests.get(
        f"{API_BASE}/getUpdates",
        params={"offset": offset, "timeout": 30},
        timeout=40,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": str(text)[:4000]}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=15)


def send_photo(chat_id, path, reply_markup=None):
    with open(path, "rb") as f:
        data = {"chat_id": chat_id}
        if reply_markup:
            import json as _json
            data["reply_markup"] = _json.dumps(reply_markup)
        requests.post(f"{API_BASE}/sendPhoto", data=data, files={"photo": f}, timeout=30)


def send_document(chat_id, path):
    with open(path, "rb") as f:
        requests.post(f"{API_BASE}/sendDocument", data={"chat_id": chat_id},
                       files={"document": f}, timeout=60)


def answer_callback_query(callback_query_id, text=None):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    requests.post(f"{API_BASE}/answerCallbackQuery", json=payload, timeout=15)


def download_telegram_file(file_id, dest_path):
    info = requests.get(f"{API_BASE}/getFile", params={"file_id": file_id}, timeout=15).json()
    file_path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    r = requests.get(url, timeout=60)
    with open(dest_path, "wb") as f:
        f.write(r.content)


def run_shell(cmd):
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                               capture_output=True, text=True, timeout=60)
        return (proc.stdout or "") + (proc.stderr or "") or "(no output)"
    except Exception as e:
        return f"Error running command: {e}"


def take_screenshot():
    import mss
    path = os.path.join(os.environ["TEMP"], "screenshot.png")
    with mss.mss() as sct:
        sct.shot(output=path)
    return path


def list_dir(path):
    try:
        path = path or "C:\\"
        entries = os.listdir(path)
        listing = "\n".join(entries) if entries else "(empty folder)"
        return f"{path}\n\n{listing[:3900]}"
    except Exception as e:
        return f"Error listing dir: {e}"


def list_dir_items(path):
    """Split a folder's contents into (folders, files), sorted, or an error string."""
    try:
        entries = os.listdir(path)
    except Exception as e:
        return None, None, str(e)
    folders, files = [], []
    for name in entries:
        full = os.path.join(path, name)
        (folders if os.path.isdir(full) else files).append(name)
    folders.sort(key=str.lower)
    files.sort(key=str.lower)
    return folders, files, None


MY_PC = "__MY_PC__"


def list_drives():
    """Return every drive letter that exists, e.g. ['C:\\\\', 'D:\\\\']."""
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    except Exception:
        return []
    return [f"{chr(65 + i)}:\\" for i in range(26) if bitmask & (1 << i)]


def is_drive_root(path):
    normalized = path.rstrip("\\/")
    return len(normalized) == 2 and normalized[1] == ":"


def build_browse_view(chat_id, path):
    """
    Build the inline keyboard for tap-to-navigate folder browsing.
    Returns (reply_markup_dict_or_None, message_text).
    Folders are tappable buttons. Files are just listed by name in the
    text (not buttons) — use 📥 Download and type the file's name to get it.
    ⬅️ Back and 📥 Download always sit at the very top so they're never
    buried under a long folder listing.
    """
    if path == MY_PC:
        drives = list_drives()
        items = [("dir", d) for d in drives]
        rows = [[{"text": f"💽 {d}", "callback_data": f"nav:{i}"}] for i, d in enumerate(drives)]
        NAV_CACHE[chat_id] = items
        rows.append([{"text": "🏠 Menu", "callback_data": "navmenu"}])
        text = "💻 My PC\n\nযে ড্রাইভে ঢুকতে চাও সেটাতে চাপ দাও।"
        return {"inline_keyboard": rows}, text

    folders, files, err = list_dir_items(path)
    if err:
        return None, f"এই path পড়া যাচ্ছে না:\n{path}\n\nError: {err}"

    items = []
    rows = [
        [{"text": "⬅️ Back", "callback_data": "navup"},
         {"text": "📥 Download", "callback_data": "dl"}],
        [{"text": "📁+ New Folder", "callback_data": "newfolder"},
         {"text": "📄+ New File", "callback_data": "newfile"}],
        [{"text": "🗑️ Delete", "callback_data": "delete"},
         {"text": "✏️ Rename", "callback_data": "rename"}],
        [{"text": "⬆️ Upload Here", "callback_data": "uploadhere"}],
    ]
    for name in folders:
        idx = len(items)
        items.append(("dir", os.path.join(path, name)))
        rows.append([{"text": f"📁 {name}", "callback_data": f"nav:{idx}"}])

    NAV_CACHE[chat_id] = items
    rows.append([{"text": "🏠 Menu", "callback_data": "navmenu"}])

    file_lines = "\n".join(f"📄 {name}" for name in files) if files else "(কোনো ফাইল নেই)"
    text = (
        f"📂 {path}\n\n"
        f"{len(folders)}টা ফোল্ডার, {len(files)}টা ফাইল\n\n"
        f"{file_lines}\n\n"
        "📥 Download-এ চাপ দিয়ে ফাইলের নাম লিখলেই সেটা পাঠিয়ে দেবো।"
    )
    return {"inline_keyboard": rows}, text


def send_browse(chat_id, path):
    path = path or MY_PC
    if path != MY_PC and not os.path.isdir(path):
        send_message(chat_id, f"এই folder নেই: {path}")
        return
    CURRENT_DIR[chat_id] = path
    kb, text = build_browse_view(chat_id, path)
    send_message(chat_id, text, reply_markup=kb)


def create_folder(path, name):
    try:
        os.makedirs(os.path.join(path, name), exist_ok=False)
        return f"✅ ফোল্ডার তৈরি হয়েছে: {name}"
    except FileExistsError:
        return f"⚠️ এই নামে আগে থেকেই আছে: {name}"
    except Exception as e:
        return f"Error: {e}"


def create_file(path, name):
    try:
        full = os.path.join(path, name)
        if os.path.exists(full):
            return f"⚠️ এই নামে আগে থেকেই আছে: {name}"
        open(full, "x").close()
        return f"✅ ফাইল তৈরি হয়েছে: {name}"
    except Exception as e:
        return f"Error: {e}"


def delete_item(path, name):
    try:
        full = os.path.join(path, name)
        if not os.path.exists(full):
            return f"⚠️ পাওয়া যায়নি: {name}"
        if os.path.isdir(full):
            import shutil
            shutil.rmtree(full)
        else:
            os.remove(full)
        return f"🗑️ ডিলিট হয়েছে: {name}"
    except Exception as e:
        return f"Error deleting: {e}"


def rename_item(path, old_name, new_name):
    try:
        old_full = os.path.join(path, old_name)
        new_full = os.path.join(path, new_name)
        if not os.path.exists(old_full):
            return f"⚠️ পাওয়া যায়নি: {old_name}"
        if os.path.exists(new_full):
            return f"⚠️ এই নামে আগে থেকেই আছে: {new_name}"
        os.rename(old_full, new_full)
        return f"✏️ নাম পরিবর্তন হয়েছে: {old_name} → {new_name}"
    except Exception as e:
        return f"Error renaming: {e}"


def open_app(name):
    try:
        os.startfile(name)
        return f"Opened: {name}"
    except Exception:
        try:
            subprocess.Popen(f"start {name}", shell=True)
            return f"Opened (fallback): {name}"
        except Exception as e2:
            return f"Could not open {name}: {e2}"


def resolve_shortcut(lnk_path):
    """Resolve a Windows .lnk shortcut to the real .exe it points to (needs pywin32)."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        return shortcut.Targetpath or None
    except Exception:
        return None


def find_chrome_exe():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        os.path.join(DESKTOP_DIR, "Google Chrome.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c


    lnk = os.path.join(DESKTOP_DIR, "Google Chrome.lnk")
    if os.path.isfile(lnk):
        target = resolve_shortcut(lnk)
        if target and os.path.isfile(target):
            return target

    return None


def google_search(query, mode="default"):
    """
    Opens Chrome to a blank tab and TYPES the query into the address bar
    (top omnibox) — it does NOT press Enter, so nothing is searched until
    you tap Enter yourself on the phone/PC. This matches "hi kemon asis"
    sitting in the address bar, not the lower Google search box.
    """
    chrome = find_chrome_exe()
    args = [chrome] if chrome else None

    try:
        if args:
            if mode == "incognito":
                args.append("--incognito")
            args.append("about:blank")
            subprocess.Popen(args)
        else:
            os.startfile("about:blank")
    except Exception as e:
        return f"Chrome খুলতে সমস্যা হয়েছে: {e}"

    time.sleep(1.5)
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.3)
        pyautogui.typewrite(query, interval=0.02)
        time.sleep(0.2)
        pyautogui.press("enter")
    except Exception as e:
        return f"Chrome খুলেছে কিন্তু address bar-এ লিখতে সমস্যা হয়েছে: {e}"

    mode_label = " (Incognito)" if mode == "incognito" else ""
    return f"🌐 Chrome{mode_label} খুলে গিয়েছে:\n{query}"


def close_app(name):
    try:
        if not name.lower().endswith(".exe"):
            name += ".exe"
        proc = subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True, text=True)
        return proc.stdout or proc.stderr or f"Closed {name}"
    except Exception as e:
        return f"Error closing {name}: {e}"


def is_screen_locked():
    """
    True if the workstation is currently locked (or on the login/secure
    desktop), False if a normal user session is active. Works by trying to
    open the input desktop with switch-access rights — that call fails
    while the screen is locked.
    """
    DESKTOP_SWITCHDESKTOP = 0x0100
    user32 = ctypes.windll.user32
    h = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    if not h:
        return True
    user32.CloseDesktop(h)
    return False


def monitor_lock_state():
    """Background thread: notify the owner whenever the lock state flips."""
    last_state = None
    while True:
        try:
            locked = is_screen_locked()
            if last_state is None:
                last_state = locked
            elif locked != last_state:
                last_state = locked
                if OWNER_CHAT_ID in AUTHENTICATED:
                    if locked:
                        send_message(OWNER_CHAT_ID, "🔒 ল্যাপটপ লক হয়েছে।")
                    else:
                        send_message(OWNER_CHAT_ID, "🔓 ল্যাপটপ আনলক হয়েছে।")
        except Exception:
            pass
        time.sleep(3)


def lock_pc():
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "🔒 ল্যাপটপ লক করে দেওয়া হয়েছে।"


def get_location():
    """Approximate IP-based location (not GPS-accurate, but works with no extra setup)."""
    try:
        r = requests.get("https://ipapi.co/json/", timeout=10)
        d = r.json()
        lat = d.get("latitude")
        lon = d.get("longitude")
        if lat is None or lon is None:
            return f"Location বের করা যায়নি।\nResponse: {d}"
        city = d.get("city", "?")
        region = d.get("region", "?")
        country = d.get("country_name", "?")
        ip = d.get("ip", "?")
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        return (
            f"📍 আনুমানিক Location (IP: {ip}):\n"
            f"{city}, {region}, {country}\n\n"
            f"{maps_url}\n\n"
            "⚠️ এটা IP-ভিত্তিক আনুমানিক লোকেশন — GPS-এর মতো নির্ভুল না।"
        )
    except Exception as e:
        return f"Location বের করতে সমস্যা হয়েছে: {e}"


_ANTITHEFT_LOCK_SCRIPT = """
import tkinter as tk

CONTACT_MSG = {contact_msg}
PIN = {pin}

root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg="#111111")
root.title("Locked")
root.protocol("WM_DELETE_WINDOW", lambda: None)

tk.Label(root, text="This laptop is locked", font=("Segoe UI", 34, "bold"),
         fg="white", bg="#111111").pack(pady=(120, 20))
tk.Label(root, text=CONTACT_MSG, font=("Segoe UI", 22), fg="white",
         bg="#111111", wraplength=1000, justify="center").pack(pady=10)

pin_var = tk.StringVar()

def try_unlock(event=None):
    if pin_var.get() == PIN:
        root.destroy()
    else:
        status_label.config(text="Wrong PIN, try again")
        pin_var.set("")

frame = tk.Frame(root, bg="#111111")
frame.pack(pady=30)
entry = tk.Entry(frame, textvariable=pin_var, show="*", font=("Segoe UI", 20), justify="center", width=12)
entry.pack(side="left", padx=10)
entry.bind("<Return>", try_unlock)
tk.Button(frame, text="Unlock", command=try_unlock, font=("Segoe UI", 14)).pack(side="left")

status_label = tk.Label(root, text="", font=("Segoe UI", 14), fg="#ff5555", bg="#111111")
status_label.pack()

entry.focus_set()
root.mainloop()
"""


ANTITHEFT_PID_FILE = os.path.join(os.environ.get("TEMP", "."), "antitheft_lock.pid")


def trigger_antitheft_lock():
    try:
        script = _ANTITHEFT_LOCK_SCRIPT.format(
            contact_msg=repr(ANTITHEFT_CONTACT_MSG),
            pin=repr(ANTITHEFT_PIN),
        )
        path = os.path.join(os.environ.get("TEMP", "."), "antitheft_lock.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        exe = pythonw if os.path.isfile(pythonw) else sys.executable
        proc = subprocess.Popen([exe, path])
        with open(ANTITHEFT_PID_FILE, "w") as f:
            f.write(str(proc.pid))
        return (
            "🚨 Anti-theft lock চালু করা হয়েছে।\n\n"
            "PIN দিয়ে লোকালি আনলক করা যাবে, অথবা এখান থেকে (Telegram) "
            "\"🔓 Remote Unlock\" বাটনে চাপ দিয়েও বন্ধ করা যাবে।\n\n"
            "নোট: এটা Task Manager দিয়েও বন্ধ করা সম্ভব, আর ল্যাপটপ ফরম্যাট/reinstall "
            "হলে পুরো bot-ই বন্ধ হয়ে যাবে — এটা guaranteed সুরক্ষা না, শুধু একটা deterrent।"
        )
    except Exception as e:
        return f"Lock চালু করতে সমস্যা হয়েছে: {e}"


def remote_unlock_antitheft():
    try:
        if not os.path.isfile(ANTITHEFT_PID_FILE):
            return "কোনো active anti-theft lock পাওয়া যায়নি।"
        with open(ANTITHEFT_PID_FILE) as f:
            pid = int(f.read().strip())
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
        try:
            os.remove(ANTITHEFT_PID_FILE)
        except Exception:
            pass
        return "🔓 Anti-theft lock দূর থেকে বন্ধ করে দেওয়া হয়েছে।"
    except Exception as e:
        return f"Remote unlock করতে সমস্যা হয়েছে: {e}"


def shutdown_pc():
    subprocess.Popen(["shutdown", "/s", "/t", "5"])
    return "Shutting down in 5 seconds..."


def restart_pc():
    subprocess.Popen(["shutdown", "/r", "/t", "5"])
    return "Restarting in 5 seconds..."


def handle_button(chat_id, label):
    if label == "📸 Screenshot":
        send_photo(chat_id, take_screenshot())

    elif label == "💻 My PC":
        send_browse(chat_id, CURRENT_DIR.get(chat_id, MY_PC))

    elif label == "🖥️ Run Command":
        PENDING[chat_id] = "shell"
        send_message(chat_id, "কী কমান্ড রান করতে চাও? লিখে পাঠাও:")

    elif label == "📂 Open App":
        PENDING[chat_id] = "open_app"
        send_message(chat_id, "কোন অ্যাপ/ফাইল ওপেন করবে? নাম লিখে পাঠাও:")

    elif label == "🌐 Chrome":
        rows = [
            [{"text": "Default (সাইন-ইন করা)", "callback_data": "gmode:default"}],
            [{"text": "Incognito (সাইন-ইন ছাড়া)", "callback_data": "gmode:incognito"}],
        ]
        send_message(chat_id, "কোনটা দিয়ে চালাবো?", reply_markup={"inline_keyboard": rows})

    elif label == "❌ Close App":
        PENDING[chat_id] = "close_app"
        send_message(chat_id, "কোন অ্যাপ বন্ধ করবে? (যেমন: notepad.exe)")

    elif label == "📥 Get File":
        PENDING[chat_id] = "get_file"
        send_message(chat_id, "কোন ফাইলের পুরো path পাঠাও:")

    elif label == "🔒 Lock PC":
        send_message(chat_id, lock_pc())

    elif label == "📍 Location":
        send_message(chat_id, get_location())

    elif label == "🚨 Anti-theft Lock":
        send_message(chat_id, trigger_antitheft_lock())

    elif label == "🔓 Remote Unlock":
        send_message(chat_id, remote_unlock_antitheft())

    elif label == "🔌 Shutdown":
        PENDING[chat_id] = "confirm_shutdown"
        send_message(chat_id, "⚠️ ল্যাপটপ শাটডাউন করবে?", reply_markup=CONFIRM_KEYBOARD)

    elif label == "🔄 Restart":
        PENDING[chat_id] = "confirm_restart"
        send_message(chat_id, "⚠️ ল্যাপটপ রিস্টার্ট করবে?", reply_markup=CONFIRM_KEYBOARD)

    elif label == "✅ Yes, do it":
        action = PENDING.pop(chat_id, None)
        if action == "confirm_shutdown":
            send_message(chat_id, shutdown_pc(), reply_markup=MAIN_KEYBOARD)
        elif action == "confirm_restart":
            send_message(chat_id, restart_pc(), reply_markup=MAIN_KEYBOARD)
        else:
            send_message(chat_id, "কিছু করার ছিল না।", reply_markup=MAIN_KEYBOARD)

    elif label == "🚫 Cancel":
        PENDING.pop(chat_id, None)
        send_message(chat_id, "বাতিল হয়েছে।", reply_markup=MAIN_KEYBOARD)

    elif label == "❓ Help":
        send_message(chat_id, HELP_TEXT)

    else:
        return False
    return True


def handle_text_command(chat_id, text):
    parts = text.strip().split(" ", 1)
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/start", "/menu"):
        send_message(chat_id, "কী করতে চাও? নিচের কীবোর্ড থেকে বেছে নাও:", reply_markup=MAIN_KEYBOARD)
    elif cmd == "/cmd":
        send_message(chat_id, run_shell(arg))
    elif cmd == "/screenshot":
        send_photo(chat_id, take_screenshot())
    elif cmd == "/ls":
        send_message(chat_id, list_dir(arg))
    elif cmd == "/open":
        send_message(chat_id, open_app(arg))
    elif cmd == "/close":
        send_message(chat_id, close_app(arg))
    elif cmd == "/search":
        send_message(chat_id, google_search(arg))
    elif cmd == "/lock":
        send_message(chat_id, lock_pc())
    elif cmd == "/shutdown":
        send_message(chat_id, shutdown_pc())
    elif cmd == "/restart":
        send_message(chat_id, restart_pc())
    elif cmd == "/get":
        if os.path.isfile(arg):
            send_document(chat_id, arg)
        else:
            send_message(chat_id, f"File not found: {arg}")
    elif cmd == "/help":
        send_message(chat_id, HELP_TEXT)
    else:
        send_message(chat_id, "চিনি না এই কমান্ড। /menu লিখে কীবোর্ড দেখো, বা /help।")


def handle_pending_reply(chat_id, text):
    action = PENDING.pop(chat_id, None)
    if action == "shell":
        send_message(chat_id, run_shell(text))
    elif action == "open_app":
        send_message(chat_id, open_app(text))
    elif action == "close_app":
        send_message(chat_id, close_app(text))
    elif action and action.startswith("google_search:"):
        mode = action.split(":", 1)[1]
        send_message(chat_id, google_search(text, mode))
    elif action and action.startswith("download_file:"):
        folder = action.split(":", 1)[1]
        full_path = os.path.join(folder, text.strip())
        if os.path.isfile(full_path):
            send_document(chat_id, full_path)
        else:
            send_message(chat_id, f"এই নামে ফাইল পাইনি: {text}")
    elif action == "get_file":
        if os.path.isfile(text):
            send_document(chat_id, text)
        else:
            send_message(chat_id, f"File not found: {text}")
    elif action and action.startswith("newfolder:"):
        path = action.split(":", 1)[1]
        send_message(chat_id, create_folder(path, text.strip()))
        send_browse(chat_id, path)
    elif action and action.startswith("newfile:"):
        path = action.split(":", 1)[1]
        send_message(chat_id, create_file(path, text.strip()))
        send_browse(chat_id, path)
    elif action and action.startswith("delete:"):
        path = action.split(":", 1)[1]
        send_message(chat_id, delete_item(path, text.strip()))
        send_browse(chat_id, path)
    elif action and action.startswith("rename_old:"):
        path = action.split(":", 1)[1]
        RENAME_STATE[chat_id] = text.strip()
        PENDING[chat_id] = f"rename_new:{path}"
        send_message(chat_id, "নতুন নাম লিখো:")
    elif action and action.startswith("rename_new:"):
        path = action.split(":", 1)[1]
        old_name = RENAME_STATE.pop(chat_id, None)
        if old_name:
            send_message(chat_id, rename_item(path, old_name, text.strip()))
        send_browse(chat_id, path)


def handle_callback(callback_query):
    chat_id = str(callback_query["message"]["chat"]["id"])
    if chat_id != OWNER_CHAT_ID:
        return
    if chat_id not in AUTHENTICATED:
        answer_callback_query(callback_query["id"], "🔒 Locked")
        return

    data = callback_query.get("data", "")
    answer_callback_query(callback_query["id"])

    if data == "navup":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            pass
        elif is_drive_root(cur):
            send_browse(chat_id, MY_PC)
        else:
            parent = os.path.dirname(cur.rstrip("\\/")) or MY_PC
            send_browse(chat_id, parent)

    elif data == "navmenu":
        send_message(chat_id, "মেনু:", reply_markup=MAIN_KEYBOARD)

    elif data == "dl":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "এখানে কোনো ফাইল নেই, আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"download_file:{cur}"
            send_message(chat_id, "কোন ফাইলের নাম লিখো (যেমন: png2.png):")

    elif data.startswith("gmode:"):
        mode = data.split(":", 1)[1]
        PENDING[chat_id] = f"google_search:{mode}"
        send_message(chat_id, "কী সার্চ করবে? লিখে পাঠাও:")

    elif data == "newfolder":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"newfolder:{cur}"
            send_message(chat_id, "নতুন ফোল্ডারের নাম লিখো:")

    elif data == "newfile":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"newfile:{cur}"
            send_message(chat_id, "নতুন ফাইলের নাম লিখো (যেমন: notes.txt):")

    elif data == "delete":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"delete:{cur}"
            send_message(chat_id, "কোন ফাইল/ফোল্ডার ডিলিট করবে? নাম লিখো:\n\n⚠️ ফোল্ডার হলে ভেতরের সবকিছুসহ ডিলিট হয়ে যাবে, ফেরত পাওয়া যাবে না।")

    elif data == "rename":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"rename_old:{cur}"
            send_message(chat_id, "কোন ফাইল/ফোল্ডারের নাম পরিবর্তন করবে? বর্তমান নাম লিখো:")

    elif data == "uploadhere":
        cur = CURRENT_DIR.get(chat_id, MY_PC)
        if cur == MY_PC:
            send_message(chat_id, "আগে কোনো ড্রাইভ/ফোল্ডারে ঢোকো।")
        else:
            PENDING[chat_id] = f"upload_here:{cur}"
            send_message(chat_id, f"যে ফাইল পাঠাবে (attach করে), সেটা এখানে সেভ হবে:\n{cur}\n\nফাইল পাঠাও:")

    elif data.startswith("nav:"):
        try:
            idx = int(data.split(":", 1)[1])
        except ValueError:
            return
        items = NAV_CACHE.get(chat_id, [])
        if idx < 0 or idx >= len(items):
            send_message(chat_id, "এই লিস্ট পুরনো হয়ে গেছে, আবার Browse করো।")
            return
        kind, full_path = items[idx]
        if kind == "dir":
            send_browse(chat_id, full_path)
        else:
            if os.path.isfile(full_path):
                send_document(chat_id, full_path)
            else:
                send_message(chat_id, f"File not found: {full_path}")


def handle_update(update):
    callback_query = update.get("callback_query")
    if callback_query:
        handle_callback(callback_query)
        return

    message = update.get("message")
    if not message:
        return

    chat_id = str(message["chat"]["id"])
    if chat_id != OWNER_CHAT_ID:
        return


    if chat_id not in AUTHENTICATED:
        text = message.get("text", "")
        if text == BOT_PASSWORD:
            AUTHENTICATED.add(chat_id)
            send_message(chat_id, "✅ Unlocked. /menu লিখে শুরু করো।", reply_markup=MAIN_KEYBOARD)
        else:
            send_message(chat_id, "🔒 Locked. প্রথমে password পাঠাও:")
        return

    if "document" in message:
        doc = message["document"]
        pending_action = PENDING.get(chat_id, "")
        if pending_action.startswith("upload_here:"):
            target_dir = pending_action.split(":", 1)[1]
            PENDING.pop(chat_id, None)
        else:
            target_dir = UPLOAD_DIR
        os.makedirs(target_dir, exist_ok=True)
        dest = os.path.join(target_dir, doc["file_name"])
        download_telegram_file(doc["file_id"], dest)
        send_message(chat_id, f"✅ Saved to {dest}")
        if pending_action.startswith("upload_here:"):
            send_browse(chat_id, target_dir)
        return

    text = message.get("text", "")
    if not text:
        return


    if handle_button(chat_id, text):
        return


    if chat_id in PENDING and not text.startswith("/"):
        handle_pending_reply(chat_id, text)
        return


    handle_text_command(chat_id, text)


def load_offset():
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE) as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def main():
    offset = load_offset()
    threading.Thread(target=monitor_lock_state, daemon=True).start()
    print("Bot started. Listening for commands...")
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                save_offset(offset)
                try:
                    handle_update(update)
                except Exception:
                    traceback.print_exc()
        except requests.exceptions.RequestException as e:
            print(f"[network error] {e}")
            time.sleep(5)
        except Exception:
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()