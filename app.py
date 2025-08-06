from flask import Flask, render_template, request, send_file, send_from_directory
import yt_dlp
import os
import uuid

app = Flask(__name__)

# إعداد مجلد التنزيلات
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تكوين خيارات التحميل لكل منصة
PLATFORM_OPTIONS = {
    'instagram': {
        'format': 'best',
        'extract_flat': True,
        'cookiesfrombrowser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave'],  # Fixed cookie option
        'add_header': [
            'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ],
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True
    },
    'tiktok': {
        'format': 'best',
        'cookies-from-browser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave'],
        'add_header': [
            'User-Agent: Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        ]
    },
    'facebook': {
        'format': 'best',
        'cookies-from-browser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave']
    },
    'youtube': {
        'format': 'best',
        'cookies-from-browser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave'],
        'cookiesfrombrowser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave'],
        'extract_flat': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'add_header': [
            'User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        ]
    },
    'twitter': {
        'format': 'best',
        'cookies-from-browser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave']
    },
    'snapchat': {
        'format': 'best',
        'cookies-from-browser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave']
    }
}

# الصفحة الرئيسية وتحميل الفيديو
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        platform = request.form['platform']
        file_name = f"{uuid.uuid4()}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        platform_opts = PLATFORM_OPTIONS.get(platform, {'format': 'best'})
        
        ydl_opts = {
            'outtmpl': file_path,
            **platform_opts
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Add error handling and info extraction
                try:
                    info = ydl.extract_info(video_url, download=False)
                    if info:
                        ydl.download([video_url])
                        return send_file(file_path, as_attachment=True)
                    else:
                        return "خطأ: لم يتم العثور على المحتوى المطلوب"
                except yt_dlp.utils.DownloadError as e:
                    return f"خطأ في التحميل: {str(e)}"
        except Exception as e:
            return f"خطأ: {str(e)}"

    return render_template('index.html')

# خدمة ملف ads.txt من الجذر
@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt')

# خدمة ملفات HTML مثل googleXXXX.html (للتحقق من Google Search Console)
@app.route('/<filename>.html')
def serve_verification_file(filename):
    return send_from_directory('static', f"{filename}.html")

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
