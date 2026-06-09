import sys
import os
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# البيانات المستخرجة بدقة من السنيفر واللوق الخاص بك
STREAM_SERVER = "http://185.243.7.190"
MAC_ADDRESS = "00:1A:79:c3:de:a5"
PLAY_TOKEN = "jtj8Knnbq9"

# الهيدرز القياسية لضمان تخطي أي حظر من السيرفر
HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb2_netfront/4.1 Safari/533.3",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def inject_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    return response

@app.route('/')
def home():
    res = Response("🚀 New Bolachas Stream Proxy: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def play_new_stream(channel_id):
    if request.method == 'OPTIONS':
        return inject_cors(Response(status=204))

    # بناء الرابط الفعلي المباشر المتطابق مع اللوق تماماً
    actual_stream_url = f"{STREAM_SERVER}/play/live.php?mac={MAC_ADDRESS}&stream={channel_id}&extension=ts&play_token={PLAY_TOKEN}"
    
    print(f"[+] جاري جلب البث المباشر من الرابط الجديد للقناة: {channel_id}", file=sys.stderr)

    def generate_chunks():
        try:
            # الاتصال المباشر بالسيرفر وبدء سحب دفق الفيديو (TS)
            with requests.get(actual_stream_url, headers=HEADERS, stream=True, timeout=(6, 30)) as r:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=32768): 
                        if chunk:
                            yield chunk
                else:
                    print(f"[-] السيرفر الأصلي أعاد خطأ استجابة: {r.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[-] انقطع الاتصال أثناء ضخ الفيديو: {e}", file=sys.stderr)

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
