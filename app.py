import sys
import os
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# البيانات المستخرجة بدقة من الـ Hex Dump
STREAM_SERVER = "http://bolachas.live"
MAC_ADDRESS = "00:1A:79:c3:de:a5"
PLAY_TOKEN = "eq5jpzIfmJ"

HEADERS = {
    "Host": "bolachas.live",
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Accept-Language": "en_US",
    "Range": "bytes=0-",
    "Connection": "keep-alive"
}

def inject_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    return response

@app.route('/')
def home():
    res = Response("🚀 Bolachas Fixed Proxy: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors(res)

# المسار الذكي: يستقبل الرابط سواء بـ /play/bolachas/ أو بالطلب المباشر
@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
@app.route('/play/live.php', methods=['GET', 'OPTIONS'])
def play_new_stream(channel_id=None):
    if request.method == 'OPTIONS':
        return inject_cors(Response(status=204))

    # إذا تم استدعاء الرابط بالصيغة القديمة، نقوم بجلب رقم القناة من الـ URL المتغير
    if not channel_id:
        channel_id = request.args.get('stream')
        
    if not channel_id:
        return inject_cors(Response("Missing Channel ID", status=400))

    # تنظيف رقم القناة من أي امتدادات مثل .ts لو وُجدت بالخطأ
    channel_id = channel_id.split('.')[0]

    actual_stream_url = f"{STREAM_SERVER}/play/live.php?mac={MAC_ADDRESS}&stream={channel_id}&extension=ts&play_token={PLAY_TOKEN}"
    print(f"[+] جاري تمرير البث المباشر للقناة: {channel_id}", file=sys.stderr)

    def generate_chunks():
        try:
            with requests.get(actual_stream_url, headers=HEADERS, stream=True, timeout=(6, 30)) as r:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=32768): 
                        if chunk:
                            yield chunk
                else:
                    print(f"[-] السيرفر الأصلي رفض الطلب بكود: {r.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[-] انقطع الاتصال أثناء تمرير البث: {e}", file=sys.stderr)

    try:
        response = Response(stream_with_context(generate_chunks()))
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return inject_cors(response)
    except Exception as e:
        return inject_cors(Response(f"Proxy Error: {str(e)}", status=500))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
