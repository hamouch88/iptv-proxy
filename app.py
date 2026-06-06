import sys
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# إعدادات سيرفر الماك أدريس والـ Stalker Portal الخاص بك
PORTAL_URL = "http://atk97.online:80/portal.php"
MAC_ADDRESS = "00:1A:79:0D:0F:7B"

# الهيدرز الإجبارية التي يطلبها سيرفر الماك ليعتقد أن خادم ريندر هو جهاز ريسيفر MAG حقيقي
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
    عمل مصادقة (Handshake) مع السيرفر الأصلي لجلب التوكن المؤقت صامتاً في الخلفية
    """
    try:
        url_auth = f"{PORTAL_URL}?type=stb&action=handshake&js=true"
        req = requests.get(url_auth, headers=STALKER_HEADERS, timeout=6)
        data = req.json()
        token = data.get('js', {}).get('token', '')
        
        if not token:
            token = data.get('result', {}).get('token', '')
            
        return token
    except Exception as e:
        print(f"[-] فشل جلب توكن الماك أدريس: {e}", file=sys.stderr)
        return None

def inject_cors(response):
    """ كسر حماية المتصفحات، المدونات، وتطبيق الأندرويد نهائياً وتفادي خطأ CORS """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'
    return response

@app.route('/')
def home():
    """ استقبال إشارة الاستيقاظ والـ Ping الاستباقي لتنشيط خادم ريندر المجاني """
    res = Response("🚀 Stalker MAC Portal Proxy Gateway: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def play_stalker_stream(channel_id):
    """
    البوابة السحرية: تستقبل المعرّف الرقمي من المشغل وتجلب دفق القناة بالتوكن والماك
    """
    if request.method == 'OPTIONS':
        return inject_cors(Response(status=204))

    # 1. جلب التوكن الحي الحالي من السيرفر الأصلي
    token = get_stalker_token()
    
    # بناء الهيدرز الكاملة مضافاً إليها التوكن وجلسة الماك أدريس معاً
    headers = STALKER_HEADERS.copy()
    if token:
        headers['Authorization'] = f"Bearer {token}"

    # 2. التكتيك المضمون: توجيه الطلب مباشرة إلى رابط تشغيل القنوات الخام بالسيرفر
    actual_stream_url = f"http://atk97.online:80/play/bolachas/{channel_id}"

    # 3. محرك ضخ وتلقيح البيانات الصامد قطرة قطرة دون استهلاك الرام
    def generate_stalker_chunks():
        try:
            # نرسل الطلب للسيرفر الأصلي محملين بالهيدرز الكاملة وجلسة الماك أدريس الحية
            with requests.get(actual_stream_url, headers=headers, stream=True, timeout=(5, 20)) as r:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                else:
                    # تكتيك احتياطي (Fallback): إذا رفض السيرفر الرابط المباشر، نجرب بوابة الـ cmd
                    fallback_url = f"{PORTAL_URL}?type=itv&action=create_link&cmd=ffmpeg%20http://localhost/ch/{channel_id}&js=true"
                    req_link = requests.get(fallback_url, headers=headers, timeout=5)
                    res_data = req_link.json()
                    link_cmd = res_data.get('js', {}).get('cmd', '').replace("ffmpeg ", "").strip()
                    
                    if link_cmd.startswith("http"):
                        with requests.get(link_cmd, headers=STALKER_HEADERS, stream=True, timeout=(5, 20)) as r2:
                            for chunk in r2.iter_content(chunk_size=8192):
                                if chunk:
                                    yield chunk
        except Exception as e:
            print(f"[-] انقطع أنبوب دفق الماك: {e}", file=sys.stderr)
        finally:
            print("[*] تم تحرير موارد البث وإغلاق الاتصال صامتاً.", file=sys.stderr)

    try:
        response = Response(stream_with_context(generate_stalker_chunks()))
        
        # تعريفات البث الحي الإجبارية للمتصفحات والمشغلات للتلقيح التلقائي
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return inject_cors(response)
    except Exception as e:
        return inject_cors(Response(f"Portal Gateway Error: {str(e)}", status=500))

if __name__ == '__main__':
    # التشغيل المحلي للمعاينة قبل الرفع لـ Render
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
