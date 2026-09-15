# ==============================================================================
# ALPHEA Connect - Master Headless Node (24/7 Automated PC Mining Daemon)
# Real-Time Visual Dashboard & Mission Progression Engine
# ==============================================================================
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import time
import datetime
import requests
import json
import random
import os
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global session_id, accumulated_seconds
        if self.path == '/restart-session':
            print('[*] [MANUAL TRIGGER] Restarting session via web request...')
            session_id = None
            accumulated_seconds = 0
            start_foreground_session()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h3>Session refreshed successfully!</h3><p>Redirecting to dashboard...</p><script>setTimeout(() => window.location.href='/', 1500);</script>")
            return
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        uptime_str = format_time(accumulated_seconds)
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ALPHEA Node Live Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .card {{ max-width: 600px; margin: 20px auto; background: #1e293b; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        h1 {{ color: #38bdf8; margin-top: 0; font-size: 24px; }}
        .stat {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }}
        .stat-label {{ color: #94a3b8; font-weight: 500; }}
        .stat-value {{ font-weight: bold; color: #4ade80; }}
        .btn {{ display: inline-block; margin-top: 20px; background: #2563eb; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 500; }}
        .btn:hover {{ background: #1d4ed8; }}
        .badge {{ background: #10b981; color: #042f2e; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h1>ALPHEA Headless Node</h1>
            <span class="badge">ONLINE 24/7</span>
        </div>
        <div class="stat"><span class="stat-label">Total Balance:</span><span class="stat-value">{cached_balance:,} Points</span></div>
        <div class="stat"><span class="stat-label">PC Session Uptime:</span><span class="stat-value">{uptime_str} ({accumulated_seconds:,}s)</span></div>
        <div class="stat"><span class="stat-label">Account:</span><span style="color:#cbd5e1;">{USER_EMAIL}</span></div>
        <div class="stat"><span class="stat-label">Device ID:</span><span style="font-family:monospace; color:#cbd5e1; font-size:12px;">{DEVICE_ID}</span></div>
        <div style="margin-top:15px; font-size:12px; color:#94a3b8;">* Auto-refreshes every 30 seconds. Managed 24/7.</div>
        <a href="/restart-session" class="btn" onclick="return confirm('Restart foreground session to reset 24h timer?')">Force Reset 24h Session</a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    def log_message(self, format, *args):
        pass

def start_health_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[!] Health server notice: {e}")

threading.Thread(target=start_health_server, daemon=True).start()

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.json')

USER_EMAIL = 'wwepubg@proton.me'
USER_ID = '9dd0fa75-0cd1-4b4e-85d3-4ec261a6dd21'
REFRESH_TOKEN = 'HQPQyQOtXUw4ArdFo0hckNB4Z7TZYzscayC0IJKDE90'
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ind3ZXB1YmdAcHJvdG9uLm1lIiwic2lkIjoiOGYzZTRjNGEtYzQ2OC00MTZjLWE2YzctODZkNmNhNmE0OGYzIiwiYXV0aF90aW1lIjoxNzg4OTc4NTUwLCJpc3MiOiJhbHBoZWEtY29ubmVjdCIsInN1YiI6IjlkZDBmYTc1LTBjZDEtNGI0ZS04NWQzLTRlYzI2MWE2ZGQyMSIsImV4cCI6MTc4ODk4MjE1MCwiaWF0IjoxNzg4OTc4NTUwfQ.hBrqg8HXKQW_ny2761g_WK-8lLmmoTRfz9jhUQBp_Dc'

# Genuine Android Hardware Identifier (16-char Hex Android ID)
DEVICE_ID = 'e4d7a8b912c3f4e5'

BASE_URL = 'https://edge.alphea.ai'
HEARTBEAT_INTERVAL = 60

session_id = None
last_token_refresh = time.time()
cached_balance = 3400
target_round_balance = 3000
accumulated_seconds = 0
last_quests_data = []

def load_session():
    global USER_EMAIL, USER_ID, DEVICE_ID, ACCESS_TOKEN, REFRESH_TOKEN
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                USER_EMAIL = data.get('email', USER_EMAIL)
                USER_ID = data.get('userId', USER_ID)
                DEVICE_ID = data.get('deviceId', DEVICE_ID)
                ACCESS_TOKEN = data.get('accessToken', ACCESS_TOKEN)
                REFRESH_TOKEN = data.get('refreshToken', REFRESH_TOKEN)
        except Exception:
            pass

def save_session():
    try:
        data = {
            'email': USER_EMAIL,
            'userId': USER_ID,
            'deviceId': DEVICE_ID,
            'accessToken': ACCESS_TOKEN,
            'refreshToken': REFRESH_TOKEN
        }
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def get_headers():
    return {
        'Content-Type': 'application/json',
        'Connect-Protocol-Version': '1',
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'User-Agent': 'okhttp/4.9.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f'{h:02d}h {m:02d}m {s:02d}s'

def render_bar(current, total, length=14):
    if total <= 0:
        pct = 100.0
    else:
        pct = min(100.0, (current / total) * 100.0)
    filled = int(round(length * (pct / 100.0)))
    bar = '=' * filled + '-' * (length - filled)
    return bar, pct

def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN, last_token_refresh
    url = f'{BASE_URL}/alphea.connect.v1.AuthService/RefreshSession'
    headers = {
        'Content-Type': 'application/json',
        'Connect-Protocol-Version': '1',
        'User-Agent': 'okhttp/4.9.2'
    }
    payload = {'refresh_token': REFRESH_TOKEN}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            data = r.json()
            ACCESS_TOKEN = data['session']['accessToken']
            new_refresh = data['session'].get('refreshToken')
            if new_refresh:
                REFRESH_TOKEN = new_refresh
            last_token_refresh = time.time()
            save_session()
            print('[*] [AUTH] Session Token refreshed! New rotated credentials auto-saved.')
            return True
        else:
            print(f'[!] [AUTH] Refresh failed: {r.status_code} {r.text}')
            return False
    except Exception as e:
        print(f'[!] [AUTH] Refresh exception: {e}')
        return False

def start_foreground_session():
    global session_id
    url = f'{BASE_URL}/alphea.connect.v1.ActivityService/StartForegroundSession'
    payload = {
        'deviceId': DEVICE_ID,
        'platform': 1  # Android Node
    }
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            session_id = data.get('sessionId')
            return True
        elif r.status_code == 401:
            if refresh_access_token():
                return start_foreground_session()
            return False
        else:
            print(f'[!] [SESSION] Start failed: {r.status_code} {r.text}')
            return False
    except Exception as e:
        print(f'[!] [SESSION] Exception: {e}')
        return False

def check_redeem_balance():
    global cached_balance, target_round_balance
    url = f'{BASE_URL}/alphea.connect.v1.RewardService/GetRedeemStatus'
    try:
        r = requests.post(url, headers=get_headers(), json={}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            balance_micros = int(data.get('balance', {}).get('micros', '0'))
            cached_balance = balance_micros // 1000000
            min_micros = int(data.get('minimum', {}).get('micros', '3000000000'))
            target_round_balance = min_micros // 1000000
    except Exception:
        pass

def fetch_and_claim_quests():
    global last_quests_data
    url = f'{BASE_URL}/alphea.connect.v1.QuestService/ListQuests'
    max_measured = 0
    try:
        r = requests.post(url, headers=get_headers(), json={}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            quests = data.get('quests', [])
            last_quests_data = quests
            for q in quests:
                qid = q.get('questId', '')
                state = q.get('state', '')
                target = int(q.get('targetValue', '0'))
                measured = int(q.get('measuredValue', '0'))
                period_key = q.get('periodKey')
                
                if 'daily-foreground' in qid:
                    if measured > max_measured:
                        max_measured = measured
                        
                # If target reached or claimable, claim immediately!
                if (measured >= target or state == 'QUEST_STATE_CLAIMABLE') and state != 'QUEST_STATE_CLAIMED':
                    claim_quest(qid, period_key)
    except Exception:
        pass
    return max_measured

def claim_quest(quest_id, period_key):
    url = f'{BASE_URL}/alphea.connect.v1.QuestService/ClaimQuest'
    payload = {
        'questId': quest_id,
        'periodKey': period_key,
        'idempotencyKey': str(uuid.uuid4())
    }
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        if r.status_code == 200:
            print(f'\n[+] [MISSION REWARD CLAIMED] Quest {quest_id} completed! Points added!')
            check_redeem_balance()
    except Exception:
        pass

def display_dashboard(session_seconds, today_seconds):
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    session_str = format_time(session_seconds)
    today_str = format_time(today_seconds)
    
    print('\n' + '=' * 72)
    print(f'[*] PC SESSION UPTIME : {session_str} ({session_seconds:,}s) | Local Node Active')
    print(f'[*] TODAY TOTAL MINED : {today_str} ({today_seconds:,}s) | Server Valid Time')
    print(f'[*] TOTAL BALANCE     : {cached_balance:,} Points | Round 3 Goal: {target_round_balance:,} Points')
    print('-' * 72)
    print('[+] MISSION / QUESTS LIVE PROGRESS (Auto-Claims when target reached):')
    
    fg_quests = [q for q in last_quests_data if 'daily-foreground' in q.get('questId', '')]
    fg_quests.sort(key=lambda x: int(x.get('targetValue', 0)))
    
    if not fg_quests:
        milestones = [
            ('1H Contribution', 3600, '+800 Pts'),
            ('3H Contribution', 10800, '+1,300 Pts'),
            ('6H Contribution', 21600, '+1,800 Pts'),
            ('12H Contribution', 43200, '+2,500 Pts'),
        ]
        for name, target, reward in milestones:
            bar, pct = render_bar(today_seconds, target)
            print(f'  |-- {name:<18} [{bar}] {pct:5.1f}% ({today_seconds}/{target}s) -> {reward}')
    else:
        for q in fg_quests:
            target = int(q.get('targetValue', '0'))
            measured = int(q.get('measuredValue', '0'))
            state = q.get('state', '')
            reward_micros = int(q.get('reward', {}).get('micros', '0'))
            reward_pts = reward_micros // 1000000
            
            hours = target // 3600
            name = f'{hours}H Contribution'
            effective_val = max(measured, today_seconds)
            bar, pct = render_bar(effective_val, target)
            
            if state == 'QUEST_STATE_CLAIMED':
                status_tag = '[CLAIMED OK]'
            elif effective_val >= target:
                status_tag = f'+{reward_pts:,} Pts [READY TO CLAIM!]'
            else:
                rem_sec = max(0, target - effective_val)
                rem_m = rem_sec // 60
                rem_s = rem_sec % 60
                status_tag = f'+{reward_pts:,} Pts [ETA: ~{rem_m}m {rem_s:02d}s]'
                
            print(f'  |-- {name:<18} [{bar}] {pct:5.1f}% ({effective_val:,}/{target:,}s) -> {status_tag}')
            
    print('=' * 72)

def submit_heartbeat():
    global session_id, accumulated_seconds
    if not session_id:
        if not start_foreground_session():
            return
            
    url = f'{BASE_URL}/alphea.connect.v1.ActivityService/SubmitHeartbeat'
    payload = {'sessionId': session_id}
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        if r.status_code == 200:
            data = r.json()
            new_seconds = int(data.get('accumulatedValidSeconds', str(accumulated_seconds)))
            
            # If 24-hour session limit reached (86,400s), rotate to fresh session for new day!
            if new_seconds >= 86400:
                print(f'\n[*] [CYCLE COMPLETE] 24-Hour limit reached ({new_seconds:,}s)!')
                print('[*] Rotating to fresh new-day session to continue mining & quests...')
                session_id = None
                accumulated_seconds = 0
                time.sleep(2)
                start_foreground_session()
                return

            accumulated_seconds = new_seconds
            today_total = fetch_and_claim_quests()
            display_dashboard(accumulated_seconds, today_total)
            print(f'[{timestamp}] [HEARTBEAT] Sync OK (200) | Valid Session Active | Next tick in 60s...')
        elif r.status_code == 400 and 'connect foreground session not active' in r.text:
            print(f'[{timestamp}] [HEARTBEAT] Session re-syncing...')
            start_foreground_session()
        elif r.status_code == 401:
            print(f'[{timestamp}] [HEARTBEAT] Auth Token expired, refreshing...')
            if refresh_access_token():
                start_foreground_session()
        else:
            print(f'[{timestamp}] [HEARTBEAT] Notice ({r.status_code}): {r.text}')
    except Exception as e:
        print(f'[!] [HEARTBEAT] Glitch: {e}')

def main():
    global session_id, accumulated_seconds
    load_session()
    print('=================================================================')
    print('ALPHEA CONNECT - HEADLESS NODE DAEMON (STEALTH ANDROID MODE)')
    print(f'User: {USER_EMAIL} (ID: {USER_ID})')
    print(f'Device: Android Galaxy Hardware ID [{DEVICE_ID}]')
    print('Emulation: OkHttp/4.9.2 Native Mobile Stack')
    print('=================================================================')
    
    check_redeem_balance()
    fetch_and_claim_quests()
    start_foreground_session()
    
    last_utc_day = datetime.datetime.now(datetime.timezone.utc).day
    tick = 0
    while True:
        try:
            # Check for UTC midnight day rollover (when daily quests reset)
            current_utc_day = datetime.datetime.now(datetime.timezone.utc).day
            if current_utc_day != last_utc_day:
                print(f'\n[*] [DAY ROLLOVER] New day detected! Resetting session for new daily rewards...')
                last_utc_day = current_utc_day
                session_id = None
                accumulated_seconds = 0
                start_foreground_session()

            if time.time() - last_token_refresh > 2700:
                refresh_access_token()
                
            submit_heartbeat()
            tick += 1
            
            if tick % 5 == 0:
                check_redeem_balance()
                
            jitter = random.uniform(-1.0, 1.0)
            time.sleep(max(30, HEARTBEAT_INTERVAL + jitter))
            
        except KeyboardInterrupt:
            print('\n[!] Node stopped by user.')
            break
        except Exception as e:
            print(f'[!] Worker error: {e}')
            time.sleep(10)

if __name__ == '__main__':
    main()
