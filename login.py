import pymysql
from functools import wraps
from flask import Blueprint, flash, redirect, render_template_string, request, session, url_for


# ============================================================
# Blueprint definition
# ============================================================
login_bp = Blueprint("login", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("username"):
            flash("Silakan login terlebih dahulu")
            return redirect(url_for("login.index"))
        return view(*args, **kwargs)
    return wrapped_view


# ============================================================
# Database configuration
# ============================================================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "db_krs"
DB_CHARSET = "utf8mb4"


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
    )


def init_database():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        charset=DB_CHARSET,
    )
    cursor = connection.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    connection.close()


def buat_tabel():
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(100)
        )
    """)

    cursor.execute("SELECT COUNT(*) AS jumlah FROM login")
    result = cursor.fetchone()
    if result and result.get("jumlah", 0) == 0:
        cursor.execute(
            "INSERT INTO login (username, password) VALUES (%s, %s)",
            ("admin", "admin123"),
        )

    conn.commit()
    cursor.close()
    conn.close()


def ambil_akun(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT username, password
        FROM login
        WHERE username = %s
        """,
        (username,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


# ============================================================
# TEMPLATE HTML LOGIN
# ============================================================
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Sistem Akademik</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
</head>
<body class="bg-soft">
<div class="app-shell">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-7 col-lg-5">
                <div class="card auth-card">
                    <div class="card-body">
                        <div class="text-center mb-5">
                            <p class="badge rounded-pill bg-primary text-white px-4 py-2">Akses Sistem</p>
                            <h1 class="h3 page-title mt-3">Login Sistem Akademik</h1>
                            <p class="page-subtitle">Masuk untuk mengelola data KRS, mahasiswa, dan mata kuliah secara cepat dan rapi.</p>
                        </div>

                        {% with messages = get_flashed_messages() %}
                            {% if messages %}
                                {% for msg in messages %}
                                    <div class="alert alert-info">{{ msg }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST" action="{{ url_for('login.login') }}">
                            <div class="mb-4">
                                <label class="form-label">Username</label>
                                <input type="text" name="username" class="form-control"
                                       placeholder="admin" required>
                            </div>
                            <div class="mb-4">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control"
                                       placeholder="admin123" required>
                            </div>
                            <div class="d-grid gap-3 d-sm-flex justify-content-sm-between">
                                <button type="submit" class="btn btn-primary btn-lg">Login</button>
                                <button type="reset" class="btn btn-outline-secondary btn-lg">Reset</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""


HTML_HOME = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Sistem Akademik</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
</head>
<body class="bg-soft">
<div class="app-shell">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-xl-6 col-lg-7 col-md-8">
                <div class="card welcome-card">
                    <div class="card-body d-flex flex-column flex-md-row align-items-center justify-content-between gap-4">
                        <div>
                            {% with messages = get_flashed_messages() %}
                                {% if messages %}
                                    {% for msg in messages %}
                                        <div class="alert alert-info">{{ msg }}</div>
                                    {% endfor %}
                                {% endif %}
                            {% endwith %}

                            <h1 class="h3 page-title">Selamat Datang</h1>
                            <p class="page-subtitle">Anda sudah login sebagai <strong>{{ username }}</strong>. Silakan gunakan menu untuk mengelola data akademik.</p>
                        </div>
                        <a href="{{ url_for('login.logout') }}" class="btn btn-danger btn-lg">Logout</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""


# ============================================================
# ROUTES
# ============================================================

@login_bp.route("/")
def index():
    if session.get("username"):
        return redirect(url_for("krs.index"))
    return render_template_string(HTML_LOGIN)


@login_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username:
        flash("Username tidak boleh kosong")
        return redirect(url_for("login.index"))

    if not password:
        flash("Password tidak boleh kosong")
        return redirect(url_for("login.index"))

    akun = ambil_akun(username)
    if akun and akun.get("password") == password:
        session["username"] = akun.get("username")
        flash("Login berhasil")
        return redirect(url_for("krs.index"))

    flash("Username atau password salah")
    return redirect(url_for("login.index"))


@login_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout berhasil")
    return redirect(url_for("login.index"))


