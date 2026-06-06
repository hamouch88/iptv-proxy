from flask import Flask, request, Response
import requests
import re
import threading
import time

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp pb.1 EmbeddedLinux"

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
        res = session.get(f"{srv['portal']}?type=stb&action=handshake", timeout=7)
        token = res.json().get('js', {}).get('token')
        return session, token
    except Exception as e:
        print(f"[-] Handshake error for {server_key}: {e}")
        return None, None

@app.route('/')
def home():
    return "IPTV Web Proxy Server is Awake & Running!", 200

@app.route('/play/<server_key>/<stream_id>')
def dynamic_proxy_stream(server_key, stream_id):
    if server_key not in SERVERS:
        return "Server not found", 404
        
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
            token_match = re.search(r'play_token=([A-Za-z0-9_-]+)', raw_cmd)
            if token_match:
                final_url = f"{srv['play_url']}/play/live.php?mac={srv['mac']}&stream={stream_id}&extension=ts&play_token={token_match.group(1)}"
            elif "/live/play/" in raw_cmd:
                clean_path = re.search(r'/live/play/[A-Za-z0-9==./_-]+', raw_cmd)
                if clean_path:
                    final_url = f"{srv['play_url']}{clean_path.group(0).strip()}"

            if final_url:
                req_headers = {"User-Agent": USER_AGENT}
                # زيادة مهلة الانتظار واستخدام تشونك أكبر لثبات مشغلات الويب
                res = requests.get(final_url, headers=req_headers, stream=True, timeout=15)
                
                def generate():
                    # كتل بيانات بحجم 64 كيلوبايت لتغذية سريعة للمشغل على المتصفح
                    for chunk in res.iter_content(chunk_size=65536):
                        if chunk:
                            yield chunk
                            
                response = Response(generate(), content_type="video/mp2t")
                
                # --- هيدرز حاسمة جداً لـ بلوجر والمشغلات الذكية لتخطي حظر CORS ---
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                return response

    except Exception as e:
        print(f"[-] Error: {e}")
        
    return "Stream unavailable", 404

def keep_server_awake():
    time.sleep(60)
    while True:
        try:
            requests.get("https://iptv-proxy-ik6e.onrender.com/", timeout=10)
        except:
            pass
        time.sleep(720)

if __name__ == '__main__':
    threading.Thread(target=keep_server_awake, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
