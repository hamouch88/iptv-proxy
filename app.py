from flask import Flask, redirect, Response
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
    # 1. بناء رابط جلب التوكن الديناميكي
    target_url = f"{BASE_URL}?mac={MAC_ADDRESS}&stream={stream_id}&extension=ts"
    
    try:
        # 2. جلب الرابط الحقيقي المشفر والتوكن من السيرفر الأصلي
        response = requests.get(target_url, headers=HEADERS, allow_redirects=False, timeout=5)
        
        if response.status_code in [301, 302] and 'Location' in response.headers:
            final_stream_url = response.headers['Location']
            
            # 3. نظام التحويل السريع (Redirect):
            # نقوم بإرسال الرابط النهائي الفرِش لتطبيقك مباشرة ليقوم بتشغيله
            # هذا يحمي ذاكرة السيرفر من الامتلاء ويمنع التقطيع تماماً
            return redirect(final_stream_url)
        else:
            return "Error: Token creation failed", 400

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
