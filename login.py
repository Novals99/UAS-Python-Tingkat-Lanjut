import pymysql
from flask import Flask, flash, redirect, render_template_string, request, session, url_for


# ============================================================
# Flask initialization
# ============================================================
app = Flask(__name__)
app.secret_key = "2512500774_secret_key"


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
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-1">Login Sistem Akademik</h4>
                    <p class="mb-0">Flask and MySQL</p>
                </div>
                <div class="card-body">
                    {% with messages = get_flashed_messages() %}
                        {% if messages %}
                            {% for msg in messages %}
                                <div class="alert alert-info">{{ msg }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}

                    <form method="POST" action="{{ url_for('login') }}">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control"
                                   placeholder="admin" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control"
                                   placeholder="admin123" required>
                        </div>
                        <div class="d-flex justify-content-between">
                            <button type="submit" class="btn btn-primary">Login</button>
                            <button type="reset" class="btn btn-secondary">Reset</button>
                        </div>
                    </form>
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
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-1">Login Sistem Akademik</h4>
                    <p class="mb-0">Flask and MySQL</p>
                </div>
                <div class="card-body">
                    {% with messages = get_flashed_messages() %}
                        {% if messages %}
                            {% for msg in messages %}
                                <div class="alert alert-info">{{ msg }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}

                    <div class="alert alert-success">
                        Anda sudah login sebagai <strong>{{ username }}</strong>.
                    </div>
                    <a href="{{ url_for('logout') }}" class="btn btn-danger">Logout</a>
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

@app.route("/")
def index():
    if session.get("username"):
        return render_template_string(
            HTML_HOME,
            username=session.get("username"),
        )
    return render_template_string(HTML_LOGIN)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username:
        flash("Username tidak boleh kosong")
        return redirect(url_for("index"))

    if not password:
        flash("Password tidak boleh kosong")
        return redirect(url_for("index"))

    akun = ambil_akun(username)
    if akun and akun.get("password") == password:
        session["username"] = akun.get("username")
        flash("Login berhasil")
        return redirect(url_for("index"))

    flash("Username atau password salah")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logout berhasil")
    return redirect(url_for("index"))


# ============================================================
# PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":
    buat_tabel()
    app.run(debug=True, port=5005)
