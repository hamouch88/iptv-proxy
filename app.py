from flask import Flask, redirect, request, Response
import requests
import re
import threading
import time

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp pb.1 EmbeddedLinux"

# قاعدة بيانات السيرفرات والماكات الشغالة الخاصة بك
SERVERS = {
    "atk": {
        "portal": "http://atk97.online:80/portal.php",
        "mac": "00:1A:79:0D:0F:7B",
        "play_url": "http://atk97.online:80"
    },
    "bolachas": {
        "portal": "http://bolachas.live:80/portal.php",
        "mac": "00:1A:79:02:a0:93", 
        "play_url": "http://bolachas.live:80"
    }
}

def get_live_token(server_key):
    srv = SERVERS[server_key]
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": f"mac={srv['mac']}",
        "Referer": srv['portal'].replace('portal.php', 'c/'),
        "Accept": "*/*"
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        # خطوة المصافحة لتوليد توكن جديد متوافق مع وقت الطلب الحالي
        res = session.get(f"{srv['portal']}?type=stb&action=handshake", timeout=7)
        token = res.json().get('js', {}).get('token')
        return session, token
    except Exception as e:
        print(f"[-] Handshake error for {server_key}: {e}")
        return None, None

# مسار الصفحة الرئيسية (مهم جداً لعملية الإيقاظ)
@app.route('/')
def home():
    return "IPTV Proxy Server is Running Smoothly & Awake!", 200

@app.route('/play/<server_key>/<stream_id>')
def dynamic_redirect(server_key, stream_id):
    if server_key not in SERVERS:
        return "Server not found", 404
        
    print(f"[*] Request received for {server_key} - Channel: {stream_id}")
    session, token = get_live_token(server_key)
    
    if not token:
        return "Handshake failed", 500
        
    srv = SERVERS[server_key]
    link_url = f"{srv['portal']}?type=itv&action=create_link&cmd=ffmpeg+http://localhost/ch/{stream_id}&token={token}"
    
    try:
        link_response = session.get(link_url, timeout=7)
        raw_cmd = link_response.json().get('js', {}).get('cmd', '')
        
        if raw_cmd:
            final_url = ""
            
            # 1. استخراج التوكن اللحظي الشغال لروابط play_token
            token_match = re.search(r'play_token=([A-Za-z0-9_-]+)', raw_cmd)
            if token_match:
                play_token = token_match.group(1)
                final_url = f"{srv['play_url']}/play/live.php?mac={srv['mac']}&stream={stream_id}&extension=ts&play_token={play_token}"
                
            # 2. إذا كان السيرفر يعتمد صيغة الـ live/play الدائرية التلقائية
            elif "/live/play/" in raw_cmd:
                clean_path = re.search(r'/live/play/[A-Za-z0-9==./_-]+', raw_cmd)
                if clean_path:
                    final_url = f"{srv['play_url']}{clean_path.group(0).strip()}"
                    
            # 3. حل احتياطي في حال أرجع السيرفر رابط HTTP مباشر
            elif "http" in raw_cmd:
                http_match = re.search(r'(http[s]?://[^\s"\']+)', raw_cmd)
                if http_match:
                    final_url = http_match.group(1)

            # إذا تم توليد الرابط بنجاح، نقوم بإرجاعه مع حزمة هيدرز كسر الحماية والتخطي
            if final_url:
                print(f"[+] Fresh URL Generated successfully: {final_url}")
                response = redirect(final_url)
                
                # --- هيدرز كسر حماية المشغلات وتخطي شاشات الحجب ---
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Bypass-Tunnel-Reminder, User-Agent, X-Requested-With"
                response.headers["Bypass-Tunnel-Reminder"] = "true"
                return response

    except Exception as e:
        print(f"[-] Error parsing link: {e}")
        
    return "Stream unavailable", 404

# --- آلية الإيقاظ الذاتي الذكية لمنع سيرفر Render من النوم ---
def keep_server_awake():
    # ننتظر دقيقة واحدة بعد تشغيل السيرفر لأول مرة لكي يستقر قبل بدء الإرسال
    time.sleep(60)
    while True:
        try:
            # السيرفر يقوم بطلب صفحته الرئيسية كل 12 دقيقة لمنع النوم الافتراضي (15 دقيقة)
            requests.get("https://iptv-proxy-ik6e.onrender.com/", timeout=10)
            print("[+] Ping sent to Render: Server is kept awake successfully.")
        except Exception as e:
            print(f"[-] Ping failed (Server might be updating): {e}")
        time.sleep(720) # 720 ثانية تعادل 12 دقيقة تماماً

if __name__ == '__main__':
    # تشغيل خيط الإيقاظ الذاتي في الخلفية
    threading.Thread(target=keep_server_awake, daemon=True).start()
    
    print("[+] Developed Dynamic Token Redirector API is Running...")
    app.run(host='0.0.0.0', port=5000, debug=False)
