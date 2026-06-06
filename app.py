import sys
import requests
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# إعدادات الوقت لمنع تجميد السيرفر (3 ثوان للاتصال، 10 ثوان لاستقبال البيانات)
TIMEOUT_CONFIG = (3, 10)

def generate_headers_from_request(client_request):
    """
    تجميع وتوليد هيدرز احترافية تطابق تماماً ما يطلبه تطبيق أندرويد حقيقي
    لتخطي حظر السيرفرات وحماية الجدار الناري
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }
    
    # تمرير هيدرز الـ Range إذا كان المشغل يطلب أجزاء معينة من الفيديو (مهم جداً للمتصفحات)
    if 'Range' in client_request.headers:
        headers['Range'] = client_request.headers['Range']
        
    return headers

def inject_cors_headers(response):
    """
    حقن الهيدرز الإجبارية لكسر حماية CORS في المدونات وتطبيق الأندرويد
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range, User-Agent, X-Requested-With'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'
    return response

@app.route('/')
def index():
    """ استقبال إشارة الاستيقاظ والـ Ping من التطبيق """
    res = Response("🚀 IPTV Proxy Gateway: ACTIVE", status=200, mimetype="text/plain")
    return inject_cors_headers(res)

@app.route('/play/bolachas/<channel_id>', methods=['GET', 'OPTIONS'])
def proxy_specific_channel(channel_id):
    if request.method == 'OPTIONS':
        return inject_cors_headers(Response(status=204))
        
    # الرابط الأصلي الذي جلبته
    target_url = f"http://91.134.195.148:8080/play/bolachas/{channel_id}"
    return execute_stream_proxy(target_url, request)

def execute_stream_proxy(target_url, client_request):
    """
    المحرك الرئيسي لضخ البيانات قطرة قطرة وعمل التلقيح التلقائي
    """
    def stream_generator():
        try:
            # محاكاة هيدرز العميل بالكامل وإرسالها للسيرفر الأصلي
            req_headers = generate_headers_from_request(client_request)
            
            with requests.get(target_url, headers=req_headers, stream=True, timeout=TIMEOUT_CONFIG) as backend_res:
                backend_res.raise_for_status()
                
                # ضخ البث على شكل كتل بحجم 4 كيلوبايت لسرعة الاستجابة ومنع انقطاع الدفق
                for chunk in backend_res.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
                    else:
                        break
        except requests.exceptions.RequestException as e:
            print(f"[-] خطأ في جلب دفق البيانات: {e}", file=sys.stderr)
        finally:
            print("[*] تم إغلاق أنبوب البث صامتاً وتحرير الموارد.", file=sys.stderr)

    try:
        response = Response(stream_with_context(stream_generator()))
        
        # تعريفات البث الحي الإجبارية للمتصفحات والمشغلات الداخلية
        response.headers['Content-Type'] = 'video/mp2t'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return inject_cors_headers(response)

    except Exception as e:
        error_res = Response(f"Gateway Error: {str(e)}", status=500)
        return inject_cors_headers(error_res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
