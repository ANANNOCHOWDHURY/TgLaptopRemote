<div align="center">
  <a href="https://www.anannochowdhury.com/">
    <img src="https://capsule-render.vercel.app/api?type=rect&height=150&color=0:0b1020,60:1a1240,100:5a46e0&text=TELEGRAM%20LAPTOP%20REMOTE%20CONTROL&fontColor=ffc857&fontSize=30&fontAlignY=45&desc=Powered%20by%20ANANNO%20CHOWDHURY&descColor=e8ebf7&descSize=16&descAlignY=72" alt="Telegram Laptop Remote Control" width="100%"/>
  </a>

<br/>

<a href="https://github.com/ANANNOCHOWDHURY">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=20&pause=1200&color=5A46E0&center=true&vCenter=true&width=640&lines=%24+whoami;Telegram+Laptop+Remote+Control;Control+your+Windows+PC+from+anywhere">
    <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=20&pause=1200&color=FFC857&center=true&vCenter=true&width=640&lines=%24+whoami;Telegram+Laptop+Remote+Control;Control+your+Windows+PC+from+anywhere" alt="$ whoami" />
  </picture>
</a>

<br/>

  <img src="https://img.shields.io/badge/status-ready-0b1020?style=for-the-badge&labelColor=0b1020&color=5a46e0" alt="status: ready"/>
  <img src="https://img.shields.io/badge/python-3.8+-0b1020?style=for-the-badge&labelColor=0b1020&color=5a46e0" alt="python 3.8+"/>
  <img src="https://img.shields.io/badge/windows-only-0b1020?style=for-the-badge&labelColor=0b1020&color=5a46e0" alt="windows only"/>

</div>

<br/>

## `> about`

A Telegram bot to remotely control your own Windows laptop — screenshots, file browsing, PowerShell commands, lock/shutdown, location, and an anti-theft lock. No separate server required — the script runs directly on your Windows laptop.

> ⚠️ Anyone who has the bot password and access can use the various remote-control features on the laptop. Use this only on your own device, or one you have explicit permission to control.

## Menu

| Button | Action |
|---|---|
| 📸 Screenshot | Take a screenshot |
| 💻 My PC | Browse drives/folders |
| 🖥️ Run Command | Run a PowerShell command |
| 🌐 Chrome | Open Chrome and search/navigate |
| 📥 Get File | Retrieve a file |
| ❌ Close App | Kill a process |
| 🔒 Lock PC | Lock the Windows session |
| 📍 Location | Show IP-based location |
| 🚨 Anti-theft Lock | PIN-protected fullscreen lock |
| 🔌 Shutdown / Restart | Shutdown or restart the PC |

## Requirements

- Your own Windows laptop/PC
- Python 3.8+
- A Telegram account
- A bot token from BotFather
- Your own Telegram Chat ID

## Setup

### Step 1 — Check if Python is installed

Open Command Prompt (cmd) and run:

```bash
python --version
```

If a version number appears, Python is installed.

If not, download and install Python from [python.org/downloads](https://www.python.org/downloads/).

During installation, make sure to check **"Add Python to PATH"**.

### Step 2 — Create a Telegram bot

1. Search for `@BotFather` on Telegram and open it.
2. Tap **Start**.
3. Send:
   ```
   /newbot
   ```
4. Give the bot a name.
5. Give it a username that ends with `bot`, for example:
   ```
   my_laptop_control_bot
   ```
6. BotFather will give you a token that looks like this:
   ```
   123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
   ```

Keep this token secret. This is your `BOT_TOKEN`.

### Step 3 — Get your Chat ID

1. Search for `@userinfobot` on Telegram.
2. Tap **Start**.
3. In the info it gives you, the number next to `Id:` is your `OWNER_CHAT_ID`.

### Step 4 — Set the configuration

Open `telegram_laptop_bot.py` in a text editor.

In the configuration section near the top, enter your own details:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_CHAT_ID = "YOUR_CHAT_ID"
BOT_PASSWORD = "YOUR_PASSWORD"
```

Example:

```python
BOT_TOKEN = "123456789:YOUR_BOT_TOKEN"
OWNER_CHAT_ID = "987654321"
BOT_PASSWORD = "MySecurePassword"
```

Then save the file.

> ⚠️ Never publish your real bot token or password to a public repository.

### Step 5 — Run the bot

Open Command Prompt in the project folder and run:

```bash
python telegram_laptop_bot.py
```

The required Python packages may be installed the first time you run it.

### Step 6 — Use it from Telegram

1. Open your Telegram bot's chat.
2. First, send the password you configured.
3. Then send:
   ```
   /menu
   ```
4. The bot's control menu will appear.

## Background Auto-start

To have the bot start automatically when Windows boots, you can use Task Scheduler.

1. Open **Task Scheduler** from the Start menu.
2. Select **Create Task...**.
3. Give the task a name under the **General** tab.
4. Go to **Triggers → New... → At log on**.
5. Go to **Actions → New...**.
6. Set the configuration as below:

   | Field | Value |
   |---|---|
   | Program/script | `pythonw.exe` |
   | Add arguments | `"C:\path\telegram_laptop_bot.py"` |
   | Start in | `C:\path\` |

7. Click **OK** to save the task.

> Using `pythonw.exe` instead of `python.exe` usually keeps the console window from showing.
>
> If something goes wrong, check the log file according to the project's logging configuration.

## Security Note

- Use this only on your own laptop/PC, or one you have the owner's permission to control.
- Do not use this to access, monitor, collect files from, or control a device without the owner's knowledge.
- Do not use this project for any harmful or illegal purpose.
- You are responsible for using this in compliance with applicable law.

## `> license`

All Rights Reserved — © 2026 Ananno Chowdhury. See [`LICENSE`](./LICENSE) for the full terms. No part of this source code, design, or content may be copied, reused, or redistributed without written permission.

## `> contact`

<div align="center">

<a href="mailto:mdnowmihayatchowdhuryananno@gmail.com"><img src="https://img.shields.io/badge/Email-8b7bff?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"/></a>
<a href="https://www.linkedin.com/in/ananno-chowdhury-6482a3378"><img src="https://img.shields.io/badge/LinkedIn-0b1020?style=for-the-badge&logo=linkedin&logoColor=ffc857" alt="LinkedIn"/></a>
<a href="https://github.com/PK-BIGBOY"><img src="https://img.shields.io/badge/GitHub-0b1020?style=for-the-badge&logo=github&logoColor=ffc857" alt="GitHub"/></a>
<a href="https://www.anannochowdhury.com/"><img src="https://img.shields.io/badge/Portfolio-0b1020?style=for-the-badge&logo=googlechrome&logoColor=ffc857" alt="Portfolio"/></a>

<br/><br/>

```bash
ananno@bigboy:~$ echo "Stay curious. Hack ethically."
Stay curious. Hack ethically.
```

<div align="center">
  <a href="https://www.anannochowdhury.com/">
    <img src="https://capsule-render.vercel.app/api?type=rect&height=80&color=0:5a46e0,40:1a1240,100:0b1020&text=Created%20by%20ANANNO%20CHOWDHURY&fontColor=ffc857&fontSize=18&fontAlignY=50" width="100%" alt="Created by ANANNO CHOWDHURY"/>
  </a>
</div>
