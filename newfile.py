from flask import Flask, request, redirect, url_for, render_template_string
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Folder where uploaded videos will be stored
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB

ALLOWED_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>TikStream</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: #000;
            color: white;
            font-family: Arial, sans-serif;
        }

        header {
            height: 60px;
            background: #111;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
        }

        .logo {
            font-size: 23px;
            font-weight: bold;
        }

        .upload-button {
            background: white;
            color: black;
            border: 0;
            border-radius: 9px;
            padding: 10px 15px;
            font-size: 16px;
            font-weight: bold;
        }

        #fileInput {
            display: none;
        }

        .feed {
            padding-top: 60px;
        }

        .video-card {
            height: calc(100vh - 60px);
            min-height: 500px;
            position: relative;
            overflow: hidden;
            background: #111;
        }

        video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .info {
            position: absolute;
            left: 15px;
            bottom: 25px;
            right: 90px;
            z-index: 5;
            text-shadow: 0 2px 5px black;
        }

        .username {
            font-size: 19px;
            font-weight: bold;
            margin-bottom: 8px;
        }

        .caption {
            font-size: 15px;
        }

        .actions {
            position: absolute;
            right: 14px;
            bottom: 65px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            text-align: center;
            z-index: 5;
        }

        .action {
            font-size: 30px;
        }

        .count {
            font-size: 13px;
            margin-top: 3px;
        }

        .empty {
            padding: 100px 20px;
            text-align: center;
            color: #aaa;
        }

        .message {
            position: fixed;
            top: 70px;
            left: 10px;
            right: 10px;
            background: #222;
            padding: 14px;
            border-radius: 10px;
            z-index: 200;
            text-align: center;
        }
    </style>
</head>

<body>

<header>
    <div class="logo">🎬 TikStream</div>

    <form
        action="/upload"
        method="POST"
        enctype="multipart/form-data"
        id="uploadForm"
    >
        <input
            id="fileInput"
            type="file"
            name="video"
            accept="video/*"
            onchange="submitVideo()"
        >

        <button
            type="button"
            class="upload-button"
            onclick="document.getElementById('fileInput').click()"
        >
            ＋ Upload
        </button>
    </form>
</header>

{% if message %}
<div class="message">
    {{ message }}
</div>
{% endif %}

<div class="feed">

{% if videos %}

    {% for video in videos %}

    <div class="video-card">

        <video
            src="{{ url_for('uploaded_file', filename=video) }}"
            controls
            loop
            playsinline
            preload="metadata">
        </video>

        <div class="info">
            <div class="username">@creator</div>
            <div class="caption">
                My uploaded video 🎬
            </div>
        </div>

        <div class="actions">
            <div>
                <div class="action">❤️</div>
                <div class="count">0</div>
            </div>

            <div>
                <div class="action">💬</div>
                <div class="count">0</div>
            </div>

            <div>
                <div class="action">↗️</div>
                <div class="count">Share</div>
            </div>
        </div>

    </div>

    {% endfor %}

{% else %}

    <div class="empty">
        <h2>No videos yet</h2>
        <p>Tap ＋ Upload to add your first video.</p>
    </div>

{% endif %}

</div>

<script>
function submitVideo() {

    const input = document.getElementById("fileInput");

    if (input.files.length === 0) {
        return;
    }

    const file = input.files[0];

    if (!file.type.startsWith("video/")) {
        alert("Please select a video file.");
        input.value = "";
        return;
    }

    if (file.size > 200 * 1024 * 1024) {
        alert("Video must be smaller than 200 MB.");
        input.value = "";
        return;
    }

    document.getElementById("uploadForm").submit();
}
</script>

</body>
</html>
"""

@app.route("/")
def home():

    videos = []

    for filename in os.listdir(UPLOAD_FOLDER):

        if allowed_file(filename):
            videos.append(filename)

    videos.sort(reverse=True)

    return render_template_string(
        HTML,
        videos=videos,
        message=request.args.get("message")
    )


@app.route("/upload", methods=["POST"])
def upload():

    if "video" not in request.files:
        return redirect(
            url_for("home", message="No video selected.")
        )

    file = request.files["video"]

    if file.filename == "":
        return redirect(
            url_for("home", message="No video selected.")
        )

    if not allowed_file(file.filename):
        return redirect(
            url_for(
                "home",
                message="Only MP4, WebM, MOV and M4V videos are allowed."
            )
        )

    filename = secure_filename(file.filename)

    # Prevent duplicate filenames
    name, extension = os.path.splitext(filename)

    counter = 1

    while os.path.exists(
        os.path.join(UPLOAD_FOLDER, filename)
    ):
        filename = f"{name}_{counter}{extension}"
        counter += 1

    file.save(
        os.path.join(UPLOAD_FOLDER, filename)
    )

    return redirect(
        url_for(
            "home",
            message="Video uploaded successfully! 🎉"
        )
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):

    from flask import send_from_directory

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )