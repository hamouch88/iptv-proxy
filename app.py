import sys
import re
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# بيانات سيرفر الماك أدريس الخاص بك
PORTAL_URL = "http://atk97.online:80/portal.php"
MAC_ADDRESS = "00:1A:79:0D:0F:7B"

# الهيدرز الإجبارية التي يطلبها سيرفر الماك ليعتقد أن الخادم هو جهاز MAG حقيقي
STALKER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb2_netfront/4.1 Safari/533.3",
    "X-User-Agent": "model=MAG250;gsw=2.18-r14-pub-250;ver=0.2.18;stb_type=pub;sn=0000000000000",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": f"mac={MAC_ADDRESS}",
    "Referer": "http://atk97.online:80/c/",
    "Connection": "keep-alive"
}

def get_stalker_token():
    """
    عمل مصادقة (Handshake) مع السيرفر الأصلي لجلب التوكن المؤقت صامتاً
    """
    try:
        # خطوة 1: طلب الـ Handshake
        url_auth = f"{PORTAL_URL}?type=stb&action=handshake&js=true"
        req = requests.get(url_auth, headers=STALKER_HEADERS, timeout=6)
        data = req.json()
        token = data.get('js', {}).get('token', '')
        
        if not token:
            # محاولة أخرى إذا كان الهيكل مختلفاً
            token = data.get('result', {}).get('token', '')
            
        return token
    except Exception as e:
        print(f"[-] فشل جلب توكن الماك أدريس: {e}", file=sys.stderr)
        return None

def inject_cors(response):
    """ كسر حماية المتصفحات والمدونات والتطبيق نهائياً """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent'
    return response

@app.route('/')
def home():
    """ إشارة الاستيقاظ والـ Ping من واجهة التطبيق """
    res = Response("🚀 Stalker MAC Portal Proxy: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def play_stalker_stream(channel_id):
    """
    البوابة السحرية: تأخذ الرقم التلقائي من واجهتك وتذهب لتوليد رابط البث الحي
    وتلقيحه وتمريره للمشغل الخرافي والتطبيق مباشرة
    """
    if request.method == 'OPTIONS':
        return inject_cors(Response(status=204))

    # 1. جلب التوكن الحي الحالي من السيرفر
    token = get_stalker_token()
    if not token:
        return inject_cors(Response("Error: Unable to authenticate with Stalker Portal.", status=403))

    # 2. بناء الهيدرز المحدثة بالتوكن الجديد لطلب رابط القناة الفعلي
    headers = STALKER_HEADERS.copy()
    headers['Authorization'] = f"Bearer {token}"

    # 3. طلب دفق رابط التشغيل الداخلي الحقيقي للقناة من السيرفر الأصلي
    # ملحوظة: السيرفرات تعتمد سكريبت cmd لجلب البث المباشر الموجه
    target_cmd_url = f"{PORTAL_URL}?type=itv&action=create_link&cmd=ffmpeg%20http://localhost/ch/{channel_id}&js=true"
    
    actual_stream_url = ""
    try:
        req_link = requests.get(target_cmd_url, headers=headers, timeout=6)
        res_data = req_link.json()
        # استخراج الرابط المباشر النهائي المخفي (غالباً يكون برابط يحتوي على باسوورد وتوكن ممتد)
        raw_url = res_data.get('js', {}).get('cmd', '') or res_data.get('result', {})
        
        # تنظيف الرابط من أي زوائد مثل كلمة 'ffmpeg' إذا وجدت
        actual_stream_url = raw_url.replace("ffmpeg ", "").strip()
        if not actual_stream_url.startswith("http"):
            # تكتيك بديل إذا كان السيرفر يرسل الرابط في خانة أخرى
            actual_stream_url = f"http://atk97.online:80/play/bolachas/{channel_id}"
            
    except Exception as e:
        print(f"[-] خطأ في استخراج رابط البث الفعلي: {e}", file=sys.stderr)
        actual_stream_url = f"http://atk97.online:80/play/bolachas/{channel_id}"

    # 4. دالة ضخ دفق الفيديو وتلقيحه تلقائياً قطرة قطرة للمتصفح والتطبيق
    def generate_stalker_chunks():
        try:
            # الاتصال بالرابط الفعلي المباشر الذي استخرجناه بالتوكن
            with requests.get(actual_stream_url, headers=STALKER_HEADERS, stream=True, timeout=(4, 15)) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
        except Exception as e:
            print(f"[-] انقطع أنبوب دفق الماك: {e}", file=sys.stderr)

    try:
        response = Response(stream_with_context(generate_stalker_chunks()))
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return inject_cors(response)
    except Exception as e:
        return inject_cors(Response(f"Portal Gateway Error: {str(e)}", status=500))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
