from flask import Flask, render_template, request, send_file, send_from_directory, redirect, url_for
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)

# إعداد مجلد التنزيلات
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تكوين خيارات التحميل لكل منصة
PLATFORM_OPTIONS = {
    'instagram': {
        'format': 'bestvideo+bestaudio/best',
        'cookiesfrombrowser': ('chrome',),
        'add_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Referer': 'https://www.instagram.com/'
        },
    },
    'tiktok': {
        'format': 'best',
        'add_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        },
    },
    'facebook': {
        'format': 'best[ext=mp4]',
        'cookiesfrombrowser': ('chrome',),
        'add_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.facebook.com/'
        }
    },
    'youtube': {
        'format': 'bestvideo+bestaudio/best',
        'add_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    },
    'twitter': {
        'format': 'best',
        'cookiesfrombrowser': ('chrome',),
        'add_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://twitter.com/'
        }
    }
}

def validate_url(url, platform):
    """التحقق من صحة الرابط وفقاً للمنصة"""
    patterns = {
        'instagram': r'(https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[^/]+/?|https?://instagr\.am/p/[^/]+/?)',
        'tiktok': r'(https?://(?:www\.|vm\.)?tiktok\.com/.+)',
        'facebook': r'(https?://(?:www\.)?facebook\.com/.+/videos/.+|https?://fb\.watch/.+)',
        'youtube': r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^&]+)',
        'twitter': r'(https?://(?:www\.)?twitter\.com/.+/status/.+|https?://(?:www\.)?x\.com/.+/status/.+)'
    }
    return re.match(patterns.get(platform, ''), url) is not None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url'].strip()
        platform = request.form['platform']
        
        if not validate_url(video_url, platform):
            return render_template('index.html', error="الرجاء إدخال رابط صحيح للمنصة المحددة")

        unique_id = uuid.uuid4()
        file_name = f"{unique_id}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        platform_opts = PLATFORM_OPTIONS.get(platform, {'format': 'best'})
        ydl_opts = {
            'outtmpl': file_path,
            'merge_output_format': 'mp4',
            'retries': 3,
            'fragment_retries': 3,
            'no_warnings': False,
            'quiet': False,
            **platform_opts
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    return render_template('index.html', error="لم يتم العثور على محتوى في هذا الرابط")
                
                if info.get('is_private', False):
                    return render_template('index.html', error="هذا المحتوى خاص ويحتاج إلى تسجيل الدخول")
                
                # التحميل الفعلي
                ydl.download([video_url])
                
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    response = send_file(
                        file_path,
                        as_attachment=True,
                        download_name=f"{info.get('title', 'video')}.mp4"
                    )
                    # حذف الملف بعد الإرسال (اختياري)
                    response.call_on_close(lambda: os.remove(file_path))
                    return response
                else:
                    return render_template('index.html', error="فشل في تحميل الفيديو")
                    
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Private' in error_msg:
                return render_template('index.html', error="هذا المحتوى خاص")
            elif 'unavailable' in error_msg.lower():
                return render_template('index.html', error="المحتوى غير متوفر أو محذوف")
            elif 'cookies' in error_msg.lower():
                return render_template('index.html', error="يحتاج إلى تسجيل الدخول (جرب من متصفحك أولاً)")
            else:
                return render_template('index.html', error=f"خطأ في التحميل: {error_msg}")
                
        except Exception as e:
            return render_template('index.html', error=f"حدث خطأ غير متوقع: {str(e)}")

    return render_template('index.html')

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt')

@app.route('/<filename>.html')
def serve_verification_file(filename):
    return send_from_directory('static', f"{filename}.html")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
