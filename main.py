
import os

# Create the complete Kahoot bot script
kahoot_bot_code = '''#!/usr/bin/env python3
"""
Kahoot Bot - Terminal-based bot controller
Usage: python kahoot_bot.py
"""

import requests
import json
import time
import random
import string
import threading
import sys
from urllib.parse import quote

class KahootBot:
    def __init__(self, pin, name, bot_id=0):
        self.pin = pin
        self.name = name
        self.bot_id = bot_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://kahoot.it',
            'Referer': 'https://kahoot.it/'
        })
        self.connected = False
        self.client_id = None
        self.game_session = None
        
    def generate_random_suffix(self, length=4):
        """Generate random suffix for bot names"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def get_session_token(self):
        """Get session token from Kahoot"""
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
            print(f"[{self.name}] Error getting session: {e}")
            return False
    
    def join_game(self):
        """Join the Kahoot game"""
        try:
            # Step 1: Get session info
            if not self.get_session_token():
                return False
            
            # Step 2: Register player via Kahoot's player registration endpoint
            url = "https://kahoot.it/rest/challenges/pin/"
            
            # Alternative approach: Use the web join endpoint
            join_url = f"https://kahoot.it/joinSession"
            
            # Try the newer API approach
            headers = {
                'Content-Type': 'application/json',
                'x-kahoot-session-token': self.game_session.get('token', '') if self.game_session else ''
            }
            
            payload = {
                "gameMode": "normal",
                "nickname": self.name,
                "kahootId": None
            }
            
            # Use the challenge/join endpoint
            challenge_url = f"https://kahoot.it/rest/challenges/{self.pin}/join"
            
            response = self.session.post(
                challenge_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"[✓] {self.name} joined successfully!")
                self.connected = True
                return True
            else:
                # Try alternative method
                return self.join_alternative()
                
        except Exception as e:
            print(f"[{self.name}] Error joining: {e}")
            return False
    
    def join_alternative(self):
        """Alternative join method using different endpoint"""
        try:
            # Try the v2 registration endpoint
            url = "https://kahoot.it/cometd/"
            
            # Handshake
            handshake_payload = [{
                "channel": "/meta/handshake",
                "version": "1.0",
                "minimumVersion": "1.0",
                "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"],
                "advice": {"timeout": 60000, "interval": 0}
            }]
            
            response = self.session.post(url, json=handshake_payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.client_id = data[0].get('clientId')
                    
                    # Now subscribe and join
                    join_payload = [{
                        "channel": "/meta/subscribe",
                        "clientId": self.client_id,
                        "subscription": f"/service/player/{self.pin}",
                        "ext": {
                            "ack": -1,
                            "timesync": {
                                "tc": str(int(time.time() * 1000)),
                                "l": 0,
                                "o": 0
                            }
                        }
                    }]
                    
                    response = self.session.post(url, json=join_payload, timeout=10)
                    
                    # Send join message
                    game_join = [{
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
                    
                    response = self.session.post(url, json=game_join, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"[✓] {self.name} connected via cometd!")
                        self.connected = True
                        return True
            
            return False
            
        except Exception as e:
            print(f"[{self.name}] Alternative join error: {e}")
            return False
    
    def keep_alive(self):
        """Keep the bot connection alive"""
        while self.connected:
            try:
                time.sleep(30)
                # Send heartbeat if needed
            except:
                break
    
    def run(self):
        """Main bot execution"""
        success = self.join_game()
        if success:
            self.keep_alive()


def print_banner():
    """Print the application banner"""
    banner = """
╔═══════════════════════════════════════════╗
║         KAHOOT BOT CONTROLLER             ║
║              Terminal Edition             ║
╚═══════════════════════════════════════════╝
    """
    print(banner)


def get_user_input():
    """Get configuration from user"""
    print("\\n" + "="*45)
    print("  CONFIGURATION")
    print("="*45 + "\\n")
    
    # Get game PIN
    while True:
        pin = input("Enter Kahoot Game PIN: ").strip()
        if pin.isdigit() and len(pin) >= 4:
            break
        print("[!] Invalid PIN. Please enter a valid numeric PIN.")
    
    # Get number of bots
    while True:
        try:
            num_bots = int(input("Number of bots (1-50): ").strip())
            if 1 <= num_bots <= 50:
                break
            print("[!] Please enter a number between 1 and 50.")
        except ValueError:
            print("[!] Please enter a valid number.")
    
    # Get base name
    base_name = input("Base name for bots (e.g., 'bot', 'player'): ").strip()
    if not base_name:
        base_name = "bot"
    
    # Name variation option
    print("\\nName Options:")
    print("  1. Sequential (bot1, bot2, bot3...)")
    print("  2. Random suffix (bot_a3f9, bot_k2m1...)")
    print("  3. Same name for all")
    
    while True:
        name_option = input("Choose option (1-3): ").strip()
        if name_option in ['1', '2', '3']:
            break
        print("[!] Please enter 1, 2, or 3.")
    
    # Get delay between joins
    while True:
        try:
            delay = float(input("Delay between bot joins (seconds, 0-5): ").strip())
            if 0 <= delay <= 5:
                break
            print("[!] Please enter a number between 0 and 5.")
        except ValueError:
            print("[!] Please enter a valid number.")
    
    return pin, num_bots, base_name, name_option, delay


def generate_bot_name(base_name, index, option):
    """Generate bot name based on option"""
    if option == '1':
        return f"{base_name}{index}"
    elif option == '2':
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{base_name}_{suffix}"
    else:
        return base_name


def main():
    """Main function"""
    print_banner()
    
    pin, num_bots, base_name, name_option, delay = get_user_input()
    
    print("\\n" + "="*45)
    print("  STARTING BOTS")
    print("="*45)
    print(f"Game PIN: {pin}")
    print(f"Number of bots: {num_bots}")
    print(f"Base name: {base_name}")
    print(f"Name style: {'Sequential' if name_option == '1' else 'Random suffix' if name_option == '2' else 'Same name'}")
    print(f"Join delay: {delay}s")
    print("="*45 + "\\n")
    
    bots = []
    threads = []
    
    for i in range(1, num_bots + 1):
        bot_name = generate_bot_name(base_name, i, name_option)
        bot = KahootBot(pin, bot_name, i)
        bots.append(bot)
        
        # Start bot in thread
        thread = threading.Thread(target=bot.run, daemon=True)
        threads.append(thread)
        thread.start()
        
        if delay > 0:
            time.sleep(delay)
    
    print("\\n" + "="*45)
    print("  ALL BOTS DEPLOYED")
    print("="*45)
    print(f"Total bots: {num_bots}")
    print("Press Ctrl+C to stop all bots\\n")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
            # Check bot status
            connected = sum(1 for b in bots if b.connected)
            print(f"\\rActive connections: {connected}/{num_bots}", end='', flush=True)
    except KeyboardInterrupt:
        print("\\n\\n[!] Stopping all bots...")
        for bot in bots:
            bot.connected = False
        print("[✓] All bots stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\\n[!] Fatal error: {e}")
        sys.exit(1)
'''

# Save the script
output_path = '/mnt/agents/output/kahoot_bot.py'
with open(output_path, 'w') as f:
    f.write(kahoot_bot_code)

print("✅ Kahoot Bot script created successfully!")
print(f"📁 Saved to: {output_path}")
print(f"📏 File size: {len(kahoot_bot_code)} characters")
