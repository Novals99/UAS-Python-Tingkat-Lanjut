from flask import Flask


# ============================================================
# Flask application initialization
# ============================================================
app = Flask(__name__)
app.secret_key = "2512500774_secret_key"


# ============================================================
# Blueprints registration
# ============================================================
import login
import krs
import mahasiswa
import matakuliah

app.register_blueprint(login.login_bp)
app.register_blueprint(krs.krs_bp)
app.register_blueprint(mahasiswa.mahasiswa_bp)
app.register_blueprint(matakuliah.matakuliah_bp)


def create_tables():
    login.buat_tabel()
    krs.buat_tabel()
    mahasiswa.buat_tabel()
    matakuliah.buat_tabel()


# ============================================================
# PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
