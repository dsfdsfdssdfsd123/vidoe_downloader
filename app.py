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

# إعدادات بسيطة لكل منصة بدون كوكيز
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
        'format': 'best[ext=mp4]/best',
        'referer': 'https://www.facebook.com/'
    },
    'youtube': {
        'format': 'best[ext=mp4][height<=1080]/best[ext=mp4]/best'
    },
    'twitter': {
        'format': 'best[ext=mp4]/best',
        'referer': 'https://twitter.com/'
    },
    'snapchat': {
        'format': 'best[ext=mp4]/best'
    }
}

# قاموس لتحديد المنصة بناءً على الأنماط في الرابط
PLATFORM_PATTERNS = {
    'instagram': r'(instagram\.com|instagr\.am)',
    'tiktok': r'tiktok\.com',
    'facebook': r'(facebook\.com|fb\.watch)',
    'youtube': r'(youtube\.com|youtu\.be)',
    'twitter': r'(twitter\.com|x\.com)',
    'snapchat': r'snapchat\.com',
}

def detect_platform(url):
    """اكتشف المنصة تلقائياً من الرابط"""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url):
            return platform
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('video_url', '').strip()
        platform = request.form.get('platform')
        
        if not video_url:
            return render_template('index.html', error_message="الرجاء إدخال رابط الفيديو.")
        
        # إذا لم يتم اختيار منصة، حاول اكتشافها تلقائياً
        if not platform:
            platform = detect_platform(video_url)
            if not platform:
                return render_template('index.html', error_message="لم نتمكن من التعرف على المنصة. الرجاء اختيارها يدوياً.")

        file_name = f"{uuid.uuid4()}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        # الحصول على إعدادات المنصة بدون كوكيز
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
                    video_title = info.get('title', f'video-{uuid.uuid4()}')
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
                    download_filename = f"{safe_title}.mp4"

                    @after_this_request
                    def cleanup(response):
                        try:
                            import time
                            time.sleep(1)
                            os.remove(file_path)
                            logging.info(f"Successfully removed temp file: {file_path}")
                        except Exception as e:
                            logging.error(f"Error removing temp file {file_path} during cleanup: {e}")
                        return response
                    
                    return send_file(file_path, as_attachment=True, download_name=download_filename)
                else:
                    logging.error(f"Download failed for URL: {video_url}. File not created or empty.")
                    return render_template('index.html', error_message="فشل في تحميل الفيديو. يرجى المحاولة مرة أخرى.")

        except yt_dlp.utils.DownloadError as e:
            error_str = str(e)
            logging.error(f"DownloadError for URL {video_url}: {error_str}")
            
            user_friendly_error = "خطأ في التحميل. تأكد من أن الرابط صحيح وأن الفيديو عام."
            if 'private' in error_str.lower() or 'login required' in error_str.lower():
                user_friendly_error = "لا يمكن تحميل الفيديو لأنه خاص أو يتطلب تسجيل الدخول."
            elif 'age' in error_str.lower() or 'restricted video' in error_str.lower():
                user_friendly_error = "هذا الفيديو مقيد بالعمر ولا يمكن تحميله بدون تسجيل الدخول."
            
            return render_template('index.html', error_message=user_friendly_error)
        except Exception as e:
            logging.exception(f"Unexpected error for URL {video_url}: {str(e)}")
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
