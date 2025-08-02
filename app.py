from flask import Flask, render_template, request, send_file, send_from_directory
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        file_name = f"{uuid.uuid4()}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        ydl_opts = {
            'outtmpl': file_path,
            'format': 'best',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            return f"خطأ: {str(e)}"

    return render_template('index.html')

# إضافة هذا المسار ليخدم ملف ads.txt من الجذر
@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
