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
        'extract_flat': True
    },
    'tiktok': {
        'format': 'best',
        'cookies-from-browser': 'chrome'
    },
    'facebook': {
        'format': 'best'
    },
    'youtube': {
        'format': 'best'
    },
    'twitter': {
        'format': 'best'
    },
    'snapchat': {
        'format': 'best'
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

        # الحصول على خيارات المنصة المحددة
        platform_opts = PLATFORM_OPTIONS.get(platform, {'format': 'best'})
        
        ydl_opts = {
            'outtmpl': file_path,
            **platform_opts
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return send_file(file_path, as_attachment=True)
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
