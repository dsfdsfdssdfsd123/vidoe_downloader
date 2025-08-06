from flask import Flask, render_template, request, send_file, send_from_directory, after_this_request
import yt_dlp
import os
import uuid
import re
import logging

app = Flask(__name__)

# إعداد نظام التسجيل (Logging) لتتبع الأخطاء وتحسين التطبيق
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# إعدادات بسيطة لكل منصة بدون كوكيز وبدون دمج
PLATFORM_SETTINGS = {
    'instagram': {
        'format': 'best[ext=mp4]/best',
        'referer': 'https://www.instagram.com/'
    },
    'tiktok': {
        'format': 'best[ext=mp4]/best',
        'referer': 'https://www.tiktok.com/'
    },
    'facebook': {
        'format': 'best[ext=mp4]/best'
    },
    'youtube': {
        'format': 'best[ext=mp4]/best'
    },
    'twitter': {
        'format': 'best[ext=mp4]/best'
    },
    'snapchat': {
        'format': 'best[ext=mp4]/best'
    }
}

# كشف المنصة من الرابط
def detect_platform(url):
    if re.search(r'(instagram\.com|instagr\.am)', url):
        return 'instagram'
    elif re.search(r'tiktok\.com', url):
        return 'tiktok'
    elif re.search(r'(facebook\.com|fb\.watch)', url):
        return 'facebook'
    elif re.search(r'(youtube\.com|youtu\.be)', url):
        return 'youtube'
    elif re.search(r'(twitter\.com|x\.com)', url):
        return 'twitter'
    elif re.search(r'snapchat\.com', url):
        return 'snapchat'
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('video_url', '').strip()
        if not video_url:
            return render_template('index.html', error_message="الرجاء إدخال رابط الفيديو.")
        
        platform = detect_platform(video_url)
        if not platform:
            return render_template('index.html', error_message="المنصة غير مدعومة أو الرابط غير صحيح.")
        
        file_name = f"{uuid.uuid4()}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        ydl_opts = {
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            **PLATFORM_SETTINGS.get(platform, {})
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if not info:
                    logging.warning(f"No content found for URL: {video_url}")
                    return render_template('index.html', error_message="لم يتم العثور على محتوى في هذا الرابط. قد يكون الفيديو خاصًا أو محذوفًا.")
                
                ydl.download([video_url])

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    @after_this_request
                    def cleanup(response):
                        try:
                            os.remove(file_path)
                            logging.info(f"Successfully removed temp file: {file_path}")
                        except Exception as e:
                            logging.error(f"Error removing file {file_path}: {e}")
                        return response
                    return send_file(file_path, as_attachment=True)
                else:
                    logging.error(f"Download failed for URL: {video_url}. File not created or empty.")
                    return render_template('index.html', error_message="فشل في تحميل الفيديو. يرجى المحاولة مرة أخرى.")

        except yt_dlp.utils.DownloadError as e:
            error_str = str(e)
            logging.error(f"DownloadError for URL {video_url}: {error_str}")
            user_friendly_error = "خطأ في التحميل. تأكد من أن الرابط صحيح وأن الفيديو عام."
            if 'private' in error_str.lower() or 'login required' in error_str.lower():
                user_friendly_error = "لا يمكن تحميل الفيديو لأنه خاص أو يتطلب تسجيل الدخول."
            return render_template('index.html', error_message=user_friendly_error)
        except Exception as e:
            logging.exception(f"Unexpected error for URL {video_url}: {str(e)}")
            # تنظيف الملف في حالة حدوث خطأ غير متوقع
            if os.path.exists(file_path):
                os.remove(file_path)
            return render_template('index.html', error_message="حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقًا.")

    return render_template('index.html')

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt')

@app.route('/<filename>.html')
def serve_verification_file(filename):
    return send_from_directory('static', f"{filename}.html")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
