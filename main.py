
import os

# Create the output directory first
os.makedirs('/mnt/agents/output', exist_ok=True)
print("✅ Directory created: /mnt/agents/output")

# Now create all files

# 1. requirements.txt
requirements = """requests>=2.31.0
"""

with open('/mnt/agents/output/requirements.txt', 'w') as f:
    f.write(requirements)
print("✅ requirements.txt created")

# 2. Procfile
procfile = """worker: python kahoot_bot.py
"""

with open('/mnt/agents/output/Procfile', 'w') as f:
    f.write(procfile)
print("✅ Procfile created")

# 3. kahoot_bot.py (Railway compatible version)
kahoot_bot = '''#!/usr/bin/env python3
"""
Kahoot Bot - Railway Compatible Version
Uses environment variables instead of interactive input
"""

import os
import requests
import json
import time
import random
import string
import threading
import sys

# Get config from environment variables
PIN = os.environ.get("KAHOOT_PIN", "")
NUM_BOTS = int(os.environ.get("KAHOOT_NUM_BOTS", "5"))
BASE_NAME = os.environ.get("KAHOOT_BASE_NAME", "bot")
NAME_OPTION = os.environ.get("KAHOOT_NAME_OPTION", "1")
JOIN_DELAY = float(os.environ.get("KAHOOT_JOIN_DELAY", "0.5"))

if not PIN:
    print("[!] ERROR: KAHOOT_PIN environment variable is required!")
    print("Set it in Railway dashboard: Variables -> KAHOOT_PIN = your_pin")
    sys.exit(1)

if NUM_BOTS < 1 or NUM_BOTS > 50:
    print("[!] ERROR: KAHOOT_NUM_BOTS must be between 1 and 50")
    sys.exit(1)


class KahootBot:
    def __init__(self, pin, name, bot_id=0):
        self.pin = pin
        self.name = name
        self.bot_id = bot_id
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://kahoot.it",
            "Referer": "https://kahoot.it/"
        })
        self.connected = False
        self.client_id = None
        self.game_session = None

    def get_session_token(self):
        try:
            url = f"https://kahoot.it/reserve/session/{self.pin}/?{int(time.time() * 1000)}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.game_session = data
                return True
            else:
                print(f"[{self.name}] Failed to get session: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return False

    def join_game(self):
        try:
            if not self.get_session_token():
                return False

            challenge_url = f"https://kahoot.it/rest/challenges/{self.pin}/join"
            headers = {
                "Content-Type": "application/json",
                "x-kahoot-session-token": self.game_session.get("token", "") if self.game_session else ""
            }
            payload = {
                "gameMode": "normal",
                "nickname": self.name,
                "kahootId": None
            }

            response = self.session.post(challenge_url, json=payload, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                print(f"[OK] {self.name} joined successfully!")
                self.connected = True
                return True
            else:
                return self.join_alternative()
        except Exception as e:
            print(f"[{self.name}] Error joining: {e}")
            return False

    def join_alternative(self):
        try:
            url = "https://kahoot.it/cometd/"
            handshake = [{
                "channel": "/meta/handshake",
                "version": "1.0",
                "minimumVersion": "1.0",
                "supportedConnectionTypes": ["websocket", "long-polling"],
                "advice": {"timeout": 60000, "interval": 0}
            }]

            response = self.session.post(url, json=handshake, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.client_id = data[0].get("clientId")
                    join_msg = [{
                        "channel": "/service/controller",
                        "clientId": self.client_id,
                        "data": {
                            "gameid": str(self.pin),
                            "host": "kahoot.it",
                            "name": self.name,
                            "type": "login"
                        },
                        "id": str(random.randint(100, 999))
                    }]
                    response = self.session.post(url, json=join_msg, timeout=10)
                    if response.status_code == 200:
                        print(f"[OK] {self.name} connected!")
                        self.connected = True
                        return True
            return False
        except Exception as e:
            print(f"[{self.name}] Alt join error: {e}")
            return False

    def keep_alive(self):
        while self.connected:
            try:
                time.sleep(30)
            except:
                break

    def run(self):
        success = self.join_game()
        if success:
            self.keep_alive()


def generate_name(base, index, option):
    if option == "1":
        return f"{base}{index}"
    elif option == "2":
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{base}_{suffix}"
    else:
        return base


def main():
    print("=" * 50)
    print("  KAHOOT BOT - Railway Deployment")
    print("=" * 50)
    print(f"PIN: {PIN}")
    print(f"Bots: {NUM_BOTS}")
    print(f"Base name: {BASE_NAME}")
    print(f"Style: {\"Sequential\" if NAME_OPTION == \"1\" else \"Random\" if NAME_OPTION == \"2\" else \"Same\"}")
    print(f"Delay: {JOIN_DELAY}s")
    print("=" * 50 + "\\n")

    bots = []
    threads = []

    for i in range(1, NUM_BOTS + 1):
        name = generate_name(BASE_NAME, i, NAME_OPTION)
        bot = KahootBot(PIN, name, i)
        bots.append(bot)

        thread = threading.Thread(target=bot.run, daemon=True)
        threads.append(thread)
        thread.start()

        if JOIN_DELAY > 0:
            time.sleep(JOIN_DELAY)

    print("\\n[OK] All bots deployed! Press Ctrl+C to stop.\\n")

    try:
        while True:
            time.sleep(5)
            connected = sum(1 for b in bots if b.connected)
            print(f"Active: {connected}/{NUM_BOTS} | {time.strftime(\"%H:%M:%S\")}")
    except KeyboardInterrupt:
        print("\\n[!] Stopping...")
        for bot in bots:
            bot.connected = False
        print("[OK] Done.")


if __name__ == "__main__":
    main()
'''

with open('/mnt/agents/output/kahoot_bot.py', 'w') as f:
    f.write(kahoot_bot)
print("✅ kahoot_bot.py created")

# Verify all files exist
print("\n📁 Files in /mnt/agents/output/:")
for f in os.listdir('/mnt/agents/output'):
    size = os.path.getsize(f'/mnt/agents/output/{f}')
    print(f"   {f} ({size} bytes)")

print("\n✅ All files created successfully!")
