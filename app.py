import sys
import time
import threading
import requests
import os
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# تحديث الرابط الجديد للبوابة والماك أدريس المستخرج
PORTAL_URL = "http://bolachas.live:80/portal.php"
MAC_ADDRESS = "00:1A:79:c3:de:a5"

STALKER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb2_netfront/4.1 Safari/533.3",
    "X-User-Agent": "model=MAG250;gsw=2.18-r14-pub-250;ver=0.2.18;stb_type=pub;sn=0000000000000",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": f"mac={MAC_ADDRESS}",
    "Referer": "http://bolachas.live:80/c/",
    "Connection": "keep-alive"
}

def get_stalker_token():
    try:
        url_auth = f"{PORTAL_URL}?type=stb&action=handshake&js=true"
        req = requests.get(url_auth, headers=STALKER_HEADERS, timeout=6)
        data = req.json()
        token = data.get('js', {}).get('token', '') or data.get('result', {}).get('token', '')
        return token
    except Exception as e:
        print(f"[-] فشل جلب توكن الماك أدريس: {e}", file=sys.stderr)
        return None

def send_keep_alive(token, channel_id, stop_event):
    headers = STALKER_HEADERS.copy()
    headers['Authorization'] = f"Bearer {token}"
    ping_url = f"{PORTAL_URL}?type=itv&action=create_link&cmd=ffmpeg%20http://localhost/ch/{channel_id}&js=true"
    
    while not stop_event.is_set():
        for _ in range(25):
            if stop_event.is_set():
                break
            time.sleep(1)
            
        if stop_event.is_set():
            break
            
        try:
            requests.get(ping_url, headers=headers, timeout=5)
            print(f"[+] تم إرسال نبضة التثبيت بنجاح للقناة {channel_id}", file=sys.stderr)
        except Exception as e:
            print(f"[-] فشل إرسال نبضة التثبيت: {e}", file=sys.stderr)

def inject_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    return response

@app.route('/')
def home():
    res = Response("🚀 Stalker Portal Proxy with Keep-Alive: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def play_stalker_stream(channel_id):
    if request.method == 'OPTIONS':
        return inject_cors(Response(status=204))

    token = get_stalker_token()
    headers = STALKER_HEADERS.copy()
    if token:
        headers['Authorization'] = f"Bearer {token}"

    actual_stream_url = f"http://bolachas.live:80/play/bolachas/{channel_id}"
    stop_event = threading.Event()

    def generate_stalker_chunks():
        try:
            if token:
                keep_alive_thread = threading.Thread(target=send_keep_alive, args=(token, channel_id, stop_event))
                keep_alive_thread.daemon = True
                keep_alive_thread.start()

            with requests.get(actual_stream_url, headers=headers, stream=True, timeout=(6, 30)) as r:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=32768): 
                        if chunk:
                            yield chunk
                else:
                    fallback_url = f"{PORTAL_URL}?type=itv&action=create_link&cmd=ffmpeg%20http://localhost/ch/{channel_id}&js=true"
                    req_link = requests.get(fallback_url, headers=headers, timeout=5)
                    link_cmd = req_link.json().get('js', {}).get('cmd', '').replace("ffmpeg ", "").strip()
                    
                    if link_cmd.startswith("http"):
                        with requests.get(link_cmd, headers=STALKER_HEADERS, stream=True, timeout=(6, 30)) as r2:
                            for chunk in r2.iter_content(chunk_size=32768):
                                if chunk:
                                    yield chunk
        except Exception as e:
            print(f"[-] انقطع دفق البيانات: {e}", file=sys.stderr)
        finally:
            stop_event.set()
            print("[*] تم تحرير جلسة التثبيت وإغلاق المسار الخارجي.", file=sys.stderr)

    try:
        response = Response(stream_with_context(generate_stalker_chunks()))
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return inject_cors(response)
    except Exception as e:
        return inject_cors(Response(f"Portal Error: {str(e)}", status=500))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
