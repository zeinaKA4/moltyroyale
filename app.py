import os
import requests
from flask import Flask, jsonify, request
from bot import MoltyBot
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Inisialisasi Bot
API_KEY = os.getenv("MOLTY_API_KEY", "")
BASE_URL = "https://mort-royal-production.up.railway.app/api"
bot = MoltyBot(api_key=API_KEY, base_url=BASE_URL)

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Molty Royale Bot Dashboard</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; max-width: 800px; margin: auto; }
                .card { background: #1e1e1e; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; }
                .log-container { background: #000; padding: 10px; height: 250px; overflow-y: scroll; font-family: 'Courier New', Courier, monospace; font-size: 12px; border-radius: 4px; }
                .status-running { color: #4caf50; font-weight: bold; }
                .status-idle { color: #ff9800; font-weight: bold; }
                button { padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; margin-right: 10px; transition: 0.3s; }
                button:hover { background: #0056b3; }
                button.secondary { background: #444; }
                button.secondary:hover { background: #555; }
                input { padding: 10px; border-radius: 4px; border: 1px solid #333; background: #222; color: white; margin-bottom: 10px; width: 100%; box-sizing: border-box; }
                .api-key-display { background: #2e7d32; color: white; padding: 15px; border-radius: 4px; margin-top: 10px; display: none; word-break: break-all; }
                h1, h2 { color: #fff; }
            </style>
        </head>
        <body>
            <h1>Molty Royale Bot</h1>
            
            <div class="card">
                <h2>1. Create Account</h2>
                <p>Belum punya API Key? Buat akun baru di sini.</p>
                <input type="text" id="new_account_name" placeholder="Masukkan Nama Akun (contoh: MyBotAgent)">
                <button onclick="createAccount()">Create Account</button>
                <div id="api_key_result" class="api-key-display">
                    <strong>PENTING! Simpan API Key Anda:</strong><br>
                    <code id="display_key"></code>
                </div>
            </div>

            <div class="card">
                <h2>2. Bot Control</h2>
                <p>Status: <span id="status" class="status-idle">Loading...</span></p>
                <p>Game ID: <span id="game_id">-</span> | Agent ID: <span id="agent_id">-</span></p>
                <button onclick="startBot()">Start Bot</button>
                <button class="secondary" onclick="stopBot()">Stop Bot</button>
            </div>

            <div class="card">
                <h2>3. Logs</h2>
                <div id="logs" class="log-container"></div>
            </div>

            <script>
                function updateStatus() {
                    fetch('/api/status')
                        .then(r => r.json())
                        .then(data => {
                            const statusEl = document.getElementById('status');
                            statusEl.innerText = data.status;
                            statusEl.className = data.status === 'Running' ? 'status-running' : 'status-idle';
                            
                            document.getElementById('game_id').innerText = data.game_id || '-';
                            document.getElementById('agent_id').innerText = data.agent_id || '-';
                            
                            const logDiv = document.getElementById('logs');
                            logDiv.innerHTML = data.logs.join('<br>');
                            logDiv.scrollTop = logDiv.scrollHeight;
                        });
                }

                function createAccount() {
                    const name = document.getElementById('new_account_name').value;
                    if(!name) return alert("Masukkan nama akun!");
                    
                    fetch('/api/create-account', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name: name})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if(data.success) {
                            const resultDiv = document.getElementById('api_key_result');
                            document.getElementById('display_key').innerText = data.apiKey;
                            resultDiv.style.display = 'block';
                            alert("Akun berhasil dibuat! Silakan simpan API Key Anda.");
                        } else {
                            alert("Gagal membuat akun: " + data.error);
                        }
                    });
                }

                function startBot() {
                    const gId = prompt("Enter Game ID:");
                    const aId = prompt("Enter Agent ID:");
                    const apiKey = prompt("Enter API Key (biarkan kosong jika sudah di-set di server):");
                    
                    if(gId && aId) {
                        fetch('/api/start', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({game_id: gId, agent_id: aId, api_key: apiKey})
                        }).then(() => updateStatus());
                    }
                }

                function stopBot() {
                    fetch('/api/stop', {method: 'POST'}).then(() => updateStatus());
                }

                setInterval(updateStatus, 3000);
                updateStatus();
            </script>
        </body>
    </html>
    """

@app.route('/api/create-account', methods=['POST'])
def create_account():
    data = request.json
    name = data.get('name')
    try:
        response = requests.post(f"{BASE_URL}/accounts", json={"name": name})
        res_data = response.json()
        if response.status_code == 201 or res_data.get('success'):
            # Molty Royale API structure: { success: true, data: { apiKey: ... } }
            account_info = res_data.get('data', {})
            return jsonify({
                "success": True, 
                "apiKey": account_info.get('apiKey'),
                "accountId": account_info.get('accountId')
            })
        else:
            return jsonify({"success": False, "error": res_data.get('message', 'Unknown error')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status')
def get_status():
    return jsonify({
        "status": bot.status,
        "game_id": bot.game_id,
        "agent_id": bot.agent_id,
        "logs": bot.logs
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    if data.get('api_key'):
        bot.api_key = data['api_key']
        bot.headers["X-API-Key"] = data['api_key']
    
    bot.start(data['game_id'], data['agent_id'])
    return jsonify({"success": True})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    bot.stop()
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
