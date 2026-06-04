from flask import Flask, Response
import requests

app = Flask(__name__)

# البيانات المستخرجة والخاصة بالسيرفر الأصلي
MAC_ADDRESS = "00:1A:79:0D:0F:7B"
BASE_URL = "http://atk97.online/play/live.php"
PACKAGE_NAME = "com.arabictvliveonlinehd"

# إعداد الهيدرز مع دمج هوية تطبيقك والـ User-Agent المناسب للسيرفر
HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; Linux; gstreamer) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 TizenX ",
    "X-Requested-With": PACKAGE_NAME,  # إرسال حزمة الهوية الرسمية لتطبيقك
    "Cookie": f"mac={MAC_ADDRESS}"
}

@app.route('/play/<stream_id>')
@app.route('/play/<stream_id>.ts')  # دعم إضافة .ts في نهاية الرابط لخدع مشغل التطبيق
def play_stream(stream_id):
    # تنظيف رقم القناة إذا كان يحتوي على امتداد .ts
    clean_stream_id = stream_id.replace('.ts', '')
    
    # 1. بناء رابط جلب التوكن الديناميكي
    target_url = f"{BASE_URL}?mac={MAC_ADDRESS}&stream={clean_stream_id}&extension=ts"
    
    try:
        # 2. جلب الرابط الحقيقي والتوكن بالهوية الجديدة
        response = requests.get(target_url, headers=HEADERS, allow_redirects=False, timeout=5)
        
        if response.status_code in [301, 302] and 'Location' in response.headers:
            final_stream_url = response.headers['Location']
            
            # 3. جلب دفق الفيديو الفعلي وتمريره
            req = requests.get(final_stream_url, headers=HEADERS, stream=True, timeout=15)
            
            def generate():
                for chunk in req.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
            
            res_headers = {
                "Connection": "keep-alive",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
                    
            return Response(generate(), content_type="video/mp2t", headers=res_headers)
        else:
            return "Error: Token creation failed", 400

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
