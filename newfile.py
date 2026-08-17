from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

# -----------------------------
# SETTINGS
# -----------------------------

app.secret_key = "change-this-secret-key"

UPLOAD_FOLDER = "uploads"
DATABASE = "users.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "mp4",
    "webm",
    "mov",
    "m4v"
}


# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------------
# HELPERS
# -----------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def current_user():
    if "user_id" not in session:
        return None

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return user


# -----------------------------
# HTML
# -----------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>TikStream</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

:root {
    --bg: #050505;
    --card: #111111;
    --card2: #181818;
    --text: #ffffff;
    --muted: #a7a7a7;
    --accent: #ff2d55;
    --accent2: #7c3aed;
    --border: rgba(255,255,255,0.08);
    --shadow: 0 20px 60px rgba(0,0,0,0.45);
}

html {
    scroll-behavior: smooth;
}

body {
    min-height: 100vh;
    background:
        radial-gradient(circle at 20% 0%, rgba(255,45,85,0.13), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(124,58,237,0.12), transparent 30%),
        var(--bg);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    overflow-x: hidden;
}

/* =========================
   TOP NAVIGATION
   ========================= */

nav,
.navbar,
header {
    position: sticky;
    top: 0;
    z-index: 1000;
    width: 100%;
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 22px;
    background: rgba(5,5,5,0.88);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-bottom: 1px solid var(--border);
}

nav a,
.navbar a,
header a {
    color: white;
    text-decoration: none;
}

nav a:hover,
.navbar a:hover,
header a:hover {
    color: #ff4d6d;
}

/* Logo */

.logo,
nav h1,
.navbar h1 {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: -1.5px;
}

.logo {
    background: linear-gradient(90deg, #ff2d55, #ff4f81, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* =========================
   MAIN CONTAINER
   ========================= */

main,
.container {
    width: min(1100px, 94%);
    margin: 0 auto;
    padding: 35px 0 100px;
}

/* =========================
   HERO / WELCOME
   ========================= */

.hero {
    position: relative;
    text-align: center;
    padding: 70px 20px 55px;
    margin-bottom: 35px;
    border: 1px solid var(--border);
    border-radius: 28px;
    overflow: hidden;
    background:
        linear-gradient(135deg,
            rgba(255,45,85,0.12),
            rgba(124,58,237,0.10),
            rgba(0,0,0,0.2));
    box-shadow: var(--shadow);
}

.hero h1 {
    font-size: clamp(38px, 8vw, 76px);
    line-height: 0.95;
    font-weight: 950;
    letter-spacing: -4px;
    margin-bottom: 18px;
}

.hero p {
    max-width: 650px;
    margin: auto;
    color: var(--muted);
    font-size: 18px;
    line-height: 1.6;
}

/* =========================
   VIDEO FEED
   ========================= */

.video-grid,
.videos {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 22px;
    margin-top: 25px;
}

.video-card,
.video {
    position: relative;
    overflow: hidden;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    box-shadow: 0 15px 45px rgba(0,0,0,0.35);
    transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
}

.video-card:hover,
.video:hover {
    transform: translateY(-6px);
    border-color: rgba(255,45,85,0.4);
    box-shadow: 0 25px 70px rgba(0,0,0,0.55);
}

video {
    display: block;
    width: 100%;
    max-height: 650px;
    background: #000;
    object-fit: cover;
}

/* =========================
   VIDEO INFORMATION
   ========================= */

.video-info {
    padding: 16px;
}

.video-info h2,
.video-info h3 {
    font-size: 17px;
    margin-bottom: 7px;
}

.video-info p {
    color: var(--muted);
    font-size: 14px;
}

/* =========================
   UPLOAD PANEL
   ========================= */

.upload,
.upload-box {
    width: 100%;
    margin: 30px auto;
    padding: 28px;
    border-radius: 24px;
    background:
        linear-gradient(145deg,
            rgba(255,255,255,0.06),
            rgba(255,255,255,0.025));
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}

.upload h2,
.upload-box h2 {
    font-size: 24px;
    margin-bottom: 8px;
}

.upload p,
.upload-box p {
    color: var(--muted);
    margin-bottom: 20px;
}

/* File picker */

input[type="file"] {
    width: 100%;
    padding: 14px;
    border-radius: 14px;
    border: 1px dashed rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.04);
    color: white;
    cursor: pointer;
}

input[type="file"]::file-selector-button {
    margin-right: 12px;
    padding: 11px 17px;
    border: none;
    border-radius: 10px;
    background: white;
    color: #111;
    font-weight: 800;
    cursor: pointer;
}

/* =========================
   BUTTONS
   ========================= */

button,
.btn,
input[type="submit"] {
    border: none;
    outline: none;
    cursor: pointer;
    padding: 13px 22px;
    border-radius: 14px;
    background: linear-gradient(135deg, #ff2d55, #ff4f81);
    color: white;
    font-size: 15px;
    font-weight: 800;
    box-shadow: 0 8px 25px rgba(255,45,85,0.25);
    transition: transform .2s ease, filter .2s ease, box-shadow .2s ease;
}

button:hover,
.btn:hover,
input[type="submit"]:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
    box-shadow: 0 12px 32px rgba(255,45,85,0.35);
}

button:active,
.btn:active,
input[type="submit"]:active {
    transform: scale(.97);
}

/* =========================
   FORMS
   ========================= */

form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

input[type="text"],
input[type="password"],
input[type="email"],
textarea,
select {
    width: 100%;
    padding: 15px 17px;
    border-radius: 14px;
    border: 1px solid var(--border);
    outline: none;
    background: #0d0d0d;
    color: white;
    font-size: 16px;
    transition: border-color .2s ease, box-shadow .2s ease;
}

input:focus,
textarea:focus,
select:focus {
    border-color: rgba(255,45,85,0.7);
    box-shadow: 0 0 0 4px rgba(255,45,85,0.10);
}

textarea {
    min-height: 110px;
    resize: vertical;
}

/* =========================
   AUTH CARDS
   ========================= */

.auth-card,
.login-card,
.signup-card {
    width: min(460px, 94%);
    margin: 70px auto;
    padding: 35px;
    border-radius: 28px;
    background:
        linear-gradient(145deg,
            rgba(255,255,255,0.07),
            rgba(255,255,255,0.025));
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}

.auth-card h1,
.login-card h1,
.signup-card h1 {
    text-align: center;
    font-size: 32px;
    margin-bottom: 25px;
}

/* =========================
   USER PROFILE
   ========================= */

.profile {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    margin-bottom: 25px;
    border-radius: 20px;
    background: rgba(255,255,255,0.045);
    border: 1px solid var(--border);
}

.avatar {
    width: 55px;
    height: 55px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff2d55, #7c3aed);
    font-size: 22px;
    font-weight: 900;
}

/* =========================
   MESSAGES / ALERTS
   ========================= */

.message,
.alert {
    padding: 14px 17px;
    margin: 15px 0;
    border-radius: 13px;
    background: rgba(255,45,85,0.10);
    border: 1px solid rgba(255,45,85,0.25);
    color: #ffd6df;
}

/* =========================
   EMPTY STATE
   ========================= */

.empty-state,
.no-videos {
    text-align: center;
    padding: 80px 20px;
    border-radius: 25px;
    border: 1px dashed rgba(255,255,255,0.14);
    background: rgba(255,255,255,0.025);
}

.empty-state h2,
.no-videos h2 {
    font-size: 30px;
    margin-bottom: 10px;
}

.empty-state p,
.no-videos p {
    color: var(--muted);
    font-size: 16px;
}

/* =========================
   LINKS
   ========================= */

a {
    color: #ff5a7d;
    transition: color .2s ease;
}

a:hover {
    color: #ff9ab0;
}

/* =========================
   SCROLLBAR
   ========================= */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #050505;
}

::-webkit-scrollbar-thumb {
    background: #292929;
    border-radius: 20px;
}

::-webkit-scrollbar-thumb:hover {
    background: #444;
}

/* =========================
   MOBILE DESIGN
   ========================= */

@media (max-width: 700px) {

    nav,
    .navbar,
    header {
        min-height: 62px;
        padding: 10px 14px;
    }

    .logo,
    nav h1,
    .navbar h1 {
        font-size: 23px;
    }

    main,
    .container {
        width: 94%;
        padding-top: 20px;
    }

    .hero {
        padding: 50px 18px;
        border-radius: 22px;
    }

    .hero h1 {
        font-size: 48px;
        letter-spacing: -2.5px;
    }

    .hero p {
        font-size: 15px;
    }

    .video-grid,
    .videos {
        grid-template-columns: 1fr;
        gap: 16px;
    }

    .upload,
    .upload-box,
    .auth-card,
    .login-card,
    .signup-card {
        padding: 22px;
        border-radius: 20px;
    }

    video {
        max-height: 75vh;
    }

    button,
    .btn,
    input[type="submit"] {
        width: 100%;
        padding: 14px;
    }
}

/* =========================
   SMALL PHONE
   ========================= */

@media (max-width: 380px) {

    .hero h1 {
        font-size: 40px;
    }

    .hero {
        padding: 40px 14px;
    }

    .upload,
    .upload-box {
        padding: 17px;
    }
}
</style>

</head>

<body>

<header>

<div class="logo">
TikStream
</div>

<div class="header-buttons">

<a class="nav-link" href="/">
Home
</a>

{% if user %}

<a class="nav-link"
href="/profile/{{ user['username'] }}">
@{{ user['username'] }}
</a>

<a class="btn"
href="/logout">
Logout
</a>

{% else %}

<a class="btn login-btn"
href="/login">
Login
</a>

<a class="btn signup-btn"
href="/signup">
Sign Up
</a>

{% endif %}

</div>

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
        controls
        autoplay
        muted
        loop
        playsinline
        preload="auto"
    >
        <source
            src="{{ url_for('uploaded_file', filename=video) }}"
            type="video/mp4"
        >
        Your browser does not support video.
    </video>

    <div class="info">

        <div class="username">
            @{{ video.split('_')[0] }}
        </div>

        <div style="display:flex; gap:10px; margin-top:12px;">

            <button
                onclick="this.classList.toggle('liked'); this.innerText = this.classList.contains('liked') ? '❤️ Liked' : '❤️ Like';"
                style="border:0; border-radius:20px; padding:9px 14px; background:#222; color:white; font-weight:600;"
            >
                ❤️ Like
            </button>

            <button
                onclick="commentVideo('{{ video }}')"
                style="border:0; border-radius:20px; padding:9px 14px; background:#222; color:white; font-weight:600;"
            >
                💬 Comment
            </button>

            <button
                onclick="shareVideo('{{ video }}')"
                style="border:0; border-radius:20px; padding:9px 14px; background:#222; color:white; font-weight:600;"
            >
                ↗️ Share
            </button>

        </div>

    </div>

</div>

</div>

{% endfor %}

{% else %}

<div style="padding:40px;text-align:center;">
<h2>No videos yet</h2>
<p>Be the first person to upload one!</p>
</div>

{% endif %}

</div>


{% if user %}

<div class="upload">

<form
action="/upload"
method="POST"
enctype="multipart/form-data">

<input
type="file"
name="video"
accept="video/*"
required>

<button type="submit">
Upload Video
</button>

</form>

</div>

{% endif %}
<script>
function commentVideo(video) {
    const comment = prompt("💬 Write your comment:");

    if (!comment || !comment.trim()) {
        return;
    }

    const key = "tikstream_comments_" + video;
    let comments = JSON.parse(localStorage.getItem(key) || "[]");

    comments.push({
        text: comment.trim(),
        time: new Date().toLocaleString()
    });

    localStorage.setItem(key, JSON.stringify(comments));

    alert("💬 Comment added successfully!");
}

function shareVideo(video) {
    const shareUrl = window.location.origin + "/";

    if (navigator.share) {
        navigator.share({
            title: "TikStream",
            text: "Check out this video on TikStream! 🎥",
            url: shareUrl
        }).catch(function() {});
    } else {
        navigator.clipboard.writeText(shareUrl)
            .then(function() {
                alert("🔗 TikStream link copied!");
            })
            .catch(function() {
                prompt("Copy this link:", shareUrl);
            });
    }
}
</script>
</body>
</html>
"""


# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():

    videos = []

    if os.path.exists(UPLOAD_FOLDER):
        videos = [
            f for f in os.listdir(UPLOAD_FOLDER)
            if allowed_file(f)
        ]

    user = current_user()

    message = request.args.get("message")

    return render_template_string(
        HTML,
        videos=videos,
        user=user,
        message=message
    )


# -----------------------------
# SIGN UP
# -----------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            return render_template_string(
                SIGNUP_HTML,
                error="Username must be at least 3 characters."
            )

        if len(password) < 6:
            return render_template_string(
                SIGNUP_HTML,
                error="Password must be at least 6 characters."
            )

        conn = get_db()

        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing:

            conn.close()

            return render_template_string(
                SIGNUP_HTML,
                error="Username already exists."
            )

        hashed_password = generate_password_hash(password)

        cursor = conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()

        user_id = cursor.lastrowid

        conn.close()

        session["user_id"] = user_id

        return redirect(url_for("home"))

    return render_template_string(
        SIGNUP_HTML,
        error=None
    )


# -----------------------------
# SIGN UP PAGE
# -----------------------------

SIGNUP_HTML = """
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Sign Up - TikStream</title>

<style>

body {
    background:#000;
    color:white;
    font-family:Arial;
}

.box {
    max-width:400px;
    margin:100px auto;
    padding:25px;
    background:#111;
    border-radius:15px;
}

input {
    width:100%;
    padding:14px;
    margin:8px 0 15px;
    border:0;
    border-radius:8px;
}

button {
    width:100%;
    padding:14px;
    border:0;
    border-radius:8px;
    font-weight:bold;
}

.error {
    background:#421818;
    padding:10px;
    border-radius:8px;
    margin-bottom:15px;
}

a {
    color:white;
}

</style>

</head>

<body>

<div class="box">

<h1>Create Account</h1>

<br>

{% if error %}
<div class="error">
{{ error }}
</div>
{% endif %}

<form method="POST">

<label>Username</label>

<input
type="text"
name="username"
placeholder="Choose a username"
required>

<label>Password</label>

<input
type="password"
name="password"
placeholder="Choose a password"
required>

<button type="submit">
Sign Up
</button>

</form>

<br>

<p>
Already have an account?
<a href="/login">Login</a>
</p>

<br>

<a href="/">← Back to TikStream</a>

</div>

</body>
</html>
"""


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            return redirect(url_for("home"))

        error = "Invalid username or password."

    return render_template_string(
        LOGIN_HTML,
        error=error
    )


# -----------------------------
# LOGIN PAGE
# -----------------------------

LOGIN_HTML = """
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Login - TikStream</title>

<style>

body {
    background:#000;
    color:white;
    font-family:Arial;
}

.box {
    max-width:400px;
    margin:100px auto;
    padding:25px;
    background:#111;
    border-radius:15px;
}

input {
    width:100%;
    padding:14px;
    margin:8px 0 15px;
    border:0;
    border-radius:8px;
}

button {
    width:100%;
    padding:14px;
    border:0;
    border-radius:8px;
    font-weight:bold;
}

.error {
    background:#421818;
    padding:10px;
    border-radius:8px;
    margin-bottom:15px;
}

a {
    color:white;
}

</style>

</head>

<body>

<div class="box">

<h1>Login</h1>

<br>

{% if error %}
<div class="error">
{{ error }}
</div>
{% endif %}

<form method="POST">

<label>Username</label>

<input
type="text"
name="username"
placeholder="Username"
required>

<label>Password</label>

<input
type="password"
name="password"
placeholder="Password"
required>

<button type="submit">
Login
</button>

</form>

<br>

<p>
Don't have an account?
<a href="/signup">Sign Up</a>
</p>

<br>

<a href="/">← Back to TikStream</a>

</div>

</body>
</html>
"""


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for(
            "home",
            message="You have been logged out."
        )
    )


# -----------------------------
# PROFILE
# -----------------------------

@app.route("/profile/<username>")
def profile(username):

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if not user:
        return "User not found", 404

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <style>
    body {{
        background:#000;
        color:white;
        font-family:Arial;
        text-align:center;
    }}

    .profile {{
        margin:100px auto;
        max-width:500px;
        background:#111;
        padding:40px;
        border-radius:20px;
    }}

    a {{
        color:white;
    }}
    </style>

    </head>

    <body>

    <div class="profile">

    <h1>@{user["username"]}</h1>

    <br>

    <p>TikStream Creator</p>

    <br>

    <a href="/">← Back to TikStream</a>

    </div>

    </body>
    </html>
    """


# -----------------------------
# UPLOAD VIDEO
# -----------------------------

@app.route("/upload", methods=["POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    file = request.files.get("video")

    if not file or file.filename == "":
        return redirect(
            url_for(
                "home",
                message="Please select a video."
            )
        )

    if not allowed_file(file.filename):
        return redirect(
            url_for(
                "home",
                message="Only MP4, WebM, MOV and M4V videos are allowed."
            )
        )

    user = current_user()

    filename = secure_filename(file.filename)

    name, extension = os.path.splitext(filename)

    # Add username to filename
    filename = f"{user['username']}_{name}{extension}"

    counter = 1

    while os.path.exists(
        os.path.join(UPLOAD_FOLDER, filename)
    ):

        filename = (
            f"{user['username']}_{name}_{counter}{extension}"
        )

        counter += 1

    file.save(
        os.path.join(
            UPLOAD_FOLDER,
            filename
        )
    )

    return redirect(
        url_for(
            "home",
            message="Video uploaded successfully!"
        )
    )


# -----------------------------
# SERVE UPLOADED VIDEOS
# -----------------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# -----------------------------
# START SERVER
# -----------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
