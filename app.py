from flask import Flask, Response
import requests

app = Flask(__name__)

MAC_ADDRESS = "00:1A:79:0D:0F:7B"
BASE_URL = "http://atk97.online/play/live.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; Linux; gstreamer) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 TizenX ",
    "Cookie": f"mac={MAC_ADDRESS}"
}

@app.route('/play/<stream_id>')
def play_stream(stream_id):
    target_url = f"{BASE_URL}?mac={MAC_ADDRESS}&stream={stream_id}&extension=ts"
    
    try:
        response = requests.get(target_url, headers=HEADERS, allow_redirects=False, timeout=5)
        
        if response.status_code in [301, 302] and 'Location' in response.headers:
            final_stream_url = response.headers['Location']
            
            # فتح اتصال البث مع السيرفر الأصلي
            req = requests.get(final_stream_url, headers=HEADERS, stream=True, timeout=15)
            
            def generate():
                # رفع الحزمة إلى 4096 لإعطاء مشغل التطبيق بيانات كافية للبدء فوراً دون استهلاك ذاكرة Render
                for chunk in req.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
            
            # إضافة هيدرز احترافية لتنبيه مشغل التطبيق بأن البث حي ومباشر ومستمر
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
