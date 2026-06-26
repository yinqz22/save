
import os

os.makedirs('/mnt/agents/output', exist_ok=True)

kahoot_bot_simple = '''#!/usr/bin/env python3
"""
Kahoot Bot - Einfache Version
Ändere PIN und NAMEN unten im Code, dann starten!
"""

import requests
import time
import random
import string
import threading

# ═══════════════════════════════════════════
# HIER KONFIGURIEREN - Einfach ändern!
# ═══════════════════════════════════════════

KAHOOT_PIN = "4717427"      # <-- Game PIN hier eingeben
BOT_NAME = "bot"             # <-- Bot Name hier eingeben
NUM_BOTS = 10                # <-- Anzahl Bots (1-50)
JOIN_DELAY = 0.5             # <-- Sekunden zwischen Joins

# ═══════════════════════════════════════════
# AB HIER NICHTS MEHR ÄNDERN!
# ═══════════════════════════════════════════


class KahootBot:
    def __init__(self, pin, name):
        self.pin = pin
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kahoot.it",
            "Referer": "https://kahoot.it/"
        })
        self.connected = False

    def get_session(self):
        try:
            url = f"https://kahoot.it/reserve/session/{self.pin}/?{int(time.time() * 1000)}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def join(self):
        try:
            session = self.get_session()
            if not session:
                print(f"[X] {self.name} - Session nicht gefunden")
                return False

            url = f"https://kahoot.it/rest/challenges/{self.pin}/join"
            headers = {"Content-Type": "application/json"}
            payload = {"gameMode": "normal", "nickname": self.name, "kahootId": None}

            response = self.session.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                print(f"[OK] {self.name} ist beigetreten!")
                self.connected = True
                return True
            else:
                # Alternative Methode
                return self.join_alt()
        except Exception as e:
            print(f"[X] {self.name} Fehler: {e}")
            return False

    def join_alt(self):
        try:
            url = "https://kahoot.it/cometd/"
            handshake = [{"channel": "/meta/handshake", "version": "1.0", "minimumVersion": "1.0",
                          "supportedConnectionTypes": ["long-polling"], "advice": {"timeout": 60000, "interval": 0}}]
            response = self.session.post(url, json=handshake, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    client_id = data[0].get("clientId")
                    join_msg = [{"channel": "/service/controller", "clientId": client_id,
                                 "data": {"gameid": str(self.pin), "host": "kahoot.it", "name": self.name, "type": "login"},
                                 "id": str(random.randint(100, 999))}]
                    response = self.session.post(url, json=join_msg, timeout=10)
                    if response.status_code == 200:
                        print(f"[OK] {self.name} verbunden!")
                        self.connected = True
                        return True
            return False
        except:
            return False

    def run(self):
        self.join()
        while self.connected:
            time.sleep(30)


def main():
    print("=" * 45)
    print("  KAHOOT BOT - Startet...")
    print("=" * 45)
    print(f"PIN: {KAHOOT_PIN}")
    print(f"Name: {BOT_NAME}")
    print(f"Bots: {NUM_BOTS}")
    print("=" * 45 + "\\n")

    bots = []
    threads = []

    for i in range(1, NUM_BOTS + 1):
        name = f"{BOT_NAME}{i}"
        bot = KahootBot(KAHOOT_PIN, name)
        bots.append(bot)

        t = threading.Thread(target=bot.run, daemon=True)
        threads.append(t)
        t.start()

        time.sleep(JOIN_DELAY)

    print(f"\\n[OK] {NUM_BOTS} Bots gestartet!")
    print("Drücke Ctrl+C zum Stoppen\\n")

    try:
        while True:
            time.sleep(5)
            online = sum(1 for b in bots if b.connected)
            print(f"Online: {online}/{NUM_BOTS}")
    except KeyboardInterrupt:
        print("\\n[!] Stoppe Bots...")
        for b in bots:
            b.connected = False
        print("[OK] Fertig!")


if __name__ == "__main__":
    main()
'''

with open('/mnt/agents/output/kahoot_bot.py', 'w') as f:
    f.write(kahoot_bot_simple)

print("✅ Einfacher Kahoot Bot erstellt!")
print("\n📁 Datei: /mnt/agents/output/kahoot_bot.py")
print("\n📝 So verwendest du es:")
print("   1. Öffne kahoot_bot.py")
print("   2. Ändere die 3 Werte ganz oben:")
print("      KAHOOT_PIN = '4693223'")
print("      BOT_NAME   = 'bot'")
print("      NUM_BOTS   = 10")
print("   3. Speichern und starten: python kahoot_bot.py")
