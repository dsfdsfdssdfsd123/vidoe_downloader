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
        'cookiefile': 'cookies.txt',  # Add cookie file option
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
        
        # Create a unique filename for both video and cookies
        unique_id = uuid.uuid4()
        file_name = f"{unique_id}.mp4"
        cookie_file = os.path.join(DOWNLOAD_FOLDER, f"cookies_{unique_id}.txt")
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        platform_opts = PLATFORM_OPTIONS.get(platform, {'format': 'best'})
        
        # Update options for better extraction
        ydl_opts = {
            'outtmpl': file_path,
            'extract_flat': False,  # Full extraction
            'format': 'best',  # Best quality
            'cookiesfrombrowser': ['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave'],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,  # Don't ignore errors to get better feedback
            **platform_opts
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # Pre-check if URL is valid
                    if not video_url or not video_url.strip():
                        return "خطأ: الرجاء إدخال رابط صحيح"

                    # Extract info first
                    info = ydl.extract_info(video_url, download=False)
                    if info:
                        # Verify we have media to download
                        if 'url' in info or 'entries' in info:
                            ydl.download([video_url])
                            if os.path.exists(file_path):
                                return send_file(file_path, as_attachment=True)
                            else:
                                return "خطأ: فشل في حفظ الملف"
                        else:
                            return "خطأ: لم يتم العثور على وسائط في الرابط"
                    else:
                        return "خطأ: لم يتم العثور على المحتوى المطلوب"
                except yt_dlp.utils.DownloadError as e:
                    error_message = str(e)
                    if "Private video" in error_message:
                        return "خطأ: هذا المحتوى خاص"
                    elif "This video is not available" in error_message:
                        return "خطأ: المحتوى غير متاح"
                    else:
                        return f"خطأ في التحميل: {error_message}"
        except Exception as e:
            return f"خطأ غير متوقع: {str(e)}"
        finally:
            # Cleanup
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            if os.path.exists(file_path) and not os.path.getsize(file_path):
                os.remove(file_path)

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
