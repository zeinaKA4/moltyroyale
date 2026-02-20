import time
import requests
import threading
import logging

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoltyBot:
    def __init__(self, api_key, base_url="https://mort-royal-production.up.railway.app/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.is_running = False
        self.status = "Idle"
        self.logs = []
        self.agent_id = None
        self.game_id = None

    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 50:
            self.logs.pop(0)
        logger.info(message)

    def get_state(self):
        if not self.game_id or not self.agent_id:
            return None
        try:
            url = f"{self.base_url}/games/{self.game_id}/agents/{self.agent_id}/state"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("data")
        except Exception as e:
            self.add_log(f"Error getting state: {e}")
        return None

    def perform_action(self, action_type, params=None):
        if not self.game_id or not self.agent_id:
            return False
        try:
            url = f"{self.base_url}/games/{self.game_id}/agents/{self.agent_id}/action"
            payload = {"type": action_type}
            if params:
                payload.update(params)
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                self.add_log(f"Action {action_type} success")
                return True
            else:
                self.add_log(f"Action {action_type} failed: {response.text}")
        except Exception as e:
            self.add_log(f"Error performing action: {e}")
        return False

    def run_loop(self):
        self.is_running = True
        self.status = "Running"
        self.add_log("Bot started")
        
        while self.is_running:
            try:
                state = self.get_state()
                if state:
                    # Logika sederhana: Jika ada item, ambil. Jika tidak, explore.
                    vision = state.get("vision", [])
                    items = [v for v in vision if v.get("type") == "item"]
                    
                    if items:
                        self.perform_action("pickup", {"targetId": items[0]["id"]})
                    else:
                        self.perform_action("explore")
                
                self.status = "Waiting for next turn (60s)"
                time.sleep(60)
            except Exception as e:
                self.add_log(f"Loop error: {e}")
                time.sleep(10)

    def start(self, game_id, agent_id):
        self.game_id = game_id
        self.agent_id = agent_id
        thread = threading.Thread(target=self.run_loop, daemon=True)
        thread.start()

    def stop(self):
        self.is_running = False
        self.status = "Stopped"
        self.add_log("Bot stopped")
