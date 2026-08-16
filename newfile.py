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

.header-buttons {
    display: flex;
    gap: 8px;
}

button,
.btn {
    background: white;
    color: black;
    border: none;
    border-radius: 9px;
    padding: 10px 15px;
    font-size: 14px;
    font-weight: bold;
    text-decoration: none;
    cursor: pointer;
}

.login-btn {
    background: #333;
    color: white;
}

.signup-btn {
    background: white;
    color: black;
}

.feed {
    padding-top: 70px;
}

.video-card {
    height: calc(100vh - 60px);
    min-height: 500px;
    position: relative;
    overflow: hidden;
    background: #111;
    margin-bottom: 5px;
}

.video-card video {
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

.profile {
    max-width: 500px;
    margin: 100px auto;
    padding: 25px;
    background: #111;
    border-radius: 15px;
}

.profile h1 {
    margin-bottom: 20px;
}

.form-box {
    max-width: 450px;
    margin: 100px auto;
    padding: 25px;
    background: #111;
    border-radius: 15px;
}

.form-box h1 {
    margin-bottom: 20px;
}

input {
    width: 100%;
    padding: 14px;
    margin: 8px 0 15px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
}

.form-box button {
    width: 100%;
    margin-top: 5px;
}

.message {
    background: #222;
    padding: 12px;
    margin: 10px;
    border-radius: 8px;
    text-align: center;
}

.upload {
    padding: 15px;
    background: #111;
    text-align: center;
}

.upload input {
    background: white;
}

.nav-link {
    color: white;
    text-decoration: none;
    margin-left: 10px;
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

<video controls playsinline preload="metadata">

<source
src="{{ url_for('uploaded_file', filename=video) }}"
type="video/mp4">

Your browser does not support video.

</video>

<div class="info">

<div class="username">
@{{ video.split('_')[0] }}
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
