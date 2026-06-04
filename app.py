from flask import Flask, Response
import requests

app = Flask(__name__)

# البيانات المستخرجة والخاصة بالسيرفر الأصلي
MAC_ADDRESS = "00:1A:79:0D:0F:7B"
BASE_URL = "http://atk97.online/play/live.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; Linux; gstreamer) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 TizenX ",
    "Cookie": f"mac={MAC_ADDRESS}"
}

@app.route('/play/<stream_id>')
def play_stream(stream_id):
    # 1. بناء رابط جلب التوكن الديناميكي بناءً على رقم القناة المطلوبة
    target_url = f"{BASE_URL}?mac={MAC_ADDRESS}&stream={stream_id}&extension=ts"
    
    try:
        # 2. جلب الرابط الحقيقي المشفر والتوكن من السيرفر الأصلي دون تتبع التحويل تلقائياً
        response = requests.get(target_url, headers=HEADERS, allow_redirects=False, timeout=5)
        
        if response.status_code in [301, 302] and 'Location' in response.headers:
            final_stream_url = response.headers['Location']
            
            # 3. نظام الـ Proxy: السيرفر السحابي يقرأ البث ويمرره للمستخدم مباشرة
            # هذا يضمن تشغيلها على أي شبكة لأن السيرفر الأصلي يرى IP سيرفر Render فقط
            req = requests.get(final_stream_url, stream=True, timeout=10)
            
            def generate():
                for chunk in req.iter_content(chunk_size=4096):
                    yield chunk
                    
            return Response(generate(), content_type="video/mp2t")
        else:
            return "Error: Token creation failed", 400

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    # تشغيل محلي للاختبار (عند رفعه على Render سيتولى gunicorn أمر التشغيل تلقائياً)
    app.run(host='0.0.0.0', port=5000)
