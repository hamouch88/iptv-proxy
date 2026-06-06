import sys
import time
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# إعدادات المزامنة والوقت لضمان عدم تجميد السيرفر
TIMEOUT_CONFIG = (6, 15) # (وقت الاتصال المبدئي، وقت انتصار دفق البيانات)

def get_clean_headers():
    """
    توليد هيدرز نظيفة ومحدثة ديناميكياً لمحاكاة المتصفحات الحقيقية
    وتفادي الحظر من السيرفرات الذكية (مثل سيرفرات الماك وياسين)
    """
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

def inject_cors_headers(response):
    """
    حقن جدار الحماية (CORS) لضمان عمل السيرفر داخل المدونات وتطبيقات الأندرويد (AppCreator24)
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'
    return response

@app.route('/')
def index():
    """
    مستقبل إشارة الاستيقاظ (Startup Ping)
    """
    res = Response("🚀 IPTV Core Proxy Gateway: ACTIVE & READY", status=200, mimetype="text/plain")
    return inject_cors_headers(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def proxy_specific_channel(channel_id):
    """
    قسم معالجة القناة المحددة (bolachas) بدقة عالية
    """
    if request.method == 'OPTIONS':
        return inject_cors_headers(Response(status=204))
        
    # الرابط الأصلي المستهدف
    target_url = f"http://91.134.195.148:8080/play/bolachas/{channel_id}"
    return execute_stream_proxy(target_url)

@app.route('/stream_gateway', methods=['GET', 'OPTIONS'])
def proxy_dynamic_channel():
    """
    [تطوير خارق] بوابة ديناميكية لتشغيل أي رابط بث خارجي آخر عبر سيرفرك
    مثال الاستخدام: https://your-server.onrender.com/stream_gateway?url=رابط_القناة_الخارجي
    """
    if request.method == 'OPTIONS':
        return inject_cors_headers(Response(status=204))

    target_url = request.args.get('url')
    if not target_url:
        res = Response("Error: Missing target stream URL parameter (?url=...)", status=400)
        return inject_cors_headers(res)
        
    return execute_stream_proxy(target_url)

def execute_stream_proxy(target_url):
    """
    المحرك الرئيسي والضخم لمعالجة وتلقيح وضخ البيانات قطرة قطرة
    """
    def stream_generator():
        client_connected = True
        try:
            # بدء طلب جلب البث من المصدر الخارجي
            with requests.get(target_url, headers=get_clean_headers(), stream=True, timeout=TIMEOUT_CONFIG) as backend_res:
                backend_res.raise_for_status()
                
                # قراءة الدفق على شكل كتل بحجم 8 كيلوبايت (حجم مثالي لتوازن السرعة مع الرام)
                for chunk in backend_res.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
                    else:
                        break
        except requests.exceptions.RequestException as e:
            print(f"[-] انقطع الاتصال بالسيرفر الموزع: {e}", file=sys.stderr)
        finally:
            print("[*] تم تحرير موارد الدفق وإغلاق الأنبوب البرمجي صامتاً.", file=sys.stderr)

    try:
        # بناء الرد التدفقي الآمن
        response = Response(stream_with_context(stream_generator()))
        
        # إعدادات هيدرز البث الحي لمنع المتصفح من حظر الرابط الرقمي الخام
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return inject_cors_headers(response)

    except Exception as e:
        error_res = Response(f"Internal Gateway Error: {str(e)}", status=500)
        return inject_cors_headers(error_res)

if __name__ == '__main__':
    # تشغيل السيرفر محلياً للمعاينة والاختبار قبل الرفع النهائي
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
