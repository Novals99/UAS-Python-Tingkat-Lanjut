import csv
import io
import pymysql
from html import escape
from flask import Flask, flash, make_response, redirect, render_template_string, request, url_for


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
        CREATE TABLE IF NOT EXISTS mahasiswa (
            nim INT PRIMARY KEY,
            nama VARCHAR(100),
            jurusan VARCHAR(100),
            fakultas VARCHAR(100)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def ambil_mahasiswa(keyword=""):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT nim, nama, jurusan, fakultas
        FROM mahasiswa
    """
    params = []

    if keyword:
        keyword_like = f"%{keyword}%"
        query += """
            WHERE CAST(nim AS CHAR) LIKE %s
               OR nama LIKE %s
               OR jurusan LIKE %s
               OR fakultas LIKE %s
        """
        params = [keyword_like] * 4

    query += " ORDER BY nim"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def ambil_mahasiswa_by_nim(nim):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT nim, nama, jurusan, fakultas
        FROM mahasiswa
        WHERE nim = %s
        """,
        (nim,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


# ============================================================
# Utility/helper functions
# ============================================================

KOLOM_CETAK = [
    "NIM", "Nama", "Jurusan", "Fakultas"
]


def format_data_row(row):
    return [
        row["nim"],
        row["nama"],
        row["jurusan"],
        row["fakultas"],
    ]


def buat_pdf_sederhana(rows):
    def escape_pdf_text(text):
        return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def format_baris(row):
        teks = " | ".join(str(value) for value in row)
        if len(teks) > 170:
            teks = teks[:167] + "..."
        return teks

    isi_baris = [
        "LAPORAN DATA MAHASISWA",
        "",
        format_baris(KOLOM_CETAK),
        "-" * 170,
    ]

    for row in rows:
        isi_baris.append(format_baris(format_data_row(row)))

    isi_baris += ["-" * 170, f"Total Mahasiswa: {len(rows)}"]

    baris_per_halaman = 34
    halaman = [isi_baris[i:i + baris_per_halaman] for i in range(0, len(isi_baris), baris_per_halaman)]

    objects = [
        (1, "<< /Type /Catalog /Pages 2 0 R >>"),
        (3, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"),
    ]
    page_ids = []
    next_id = 4

    for lines in halaman:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)

        content = ["BT", "/F1 8 Tf", "40 555 Td", "12 TL"]
        for line in lines:
            content.append(f"({escape_pdf_text(line)}) Tj")
            content.append("T*")
        content.append("ET")

        stream = "\n".join(content).encode("latin-1", "replace")
        objects.append((content_id, f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream"))
        objects.append((page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"))

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.insert(1, (2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"))

    objects.sort(key=lambda x: x[0])

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for object_id, obj in objects:
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        pdf.extend(obj.encode("latin-1", "replace"))
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    max_id = max(object_id for object_id, _ in objects)
    pdf.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    offset_map = {object_id: offset for object_id, offset in zip([obj[0] for obj in objects], offsets)}
    for object_id in range(1, max_id + 1):
        pdf.extend(f"{offset_map.get(object_id, 0):010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(pdf)


# ============================================================
# TEMPLATE HTML UTAMA
# ============================================================

HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Form Data Mahasiswa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4 mb-5">
    <h3>Form Data Mahasiswa - Flask dan MySQL</h3>
    <p class="text-muted">
        CRUD tabel Mahasiswa menggunakan primary key NIM.
    </p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="card mb-3">
        <div class="card-header bg-primary text-white">Input Data Mahasiswa</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('simpan') }}">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>NIM</label>
                        <input type="number" name="nim" class="form-control"
                               placeholder="123456" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Nama</label>
                        <input type="text" name="nama" class="form-control"
                               placeholder="Nama Mahasiswa" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Jurusan</label>
                        <input type="text" name="jurusan" class="form-control"
                               placeholder="Jurusan" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Fakultas</label>
                        <input type="text" name="fakultas" class="form-control"
                               placeholder="Fakultas" required>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12 mb-2 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary me-2">Simpan</button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">Reset</a>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <form method="GET" action="{{ url_for('index') }}" class="mb-3">
        <div class="input-group">
            <input type="text" name="keyword" class="form-control"
                   placeholder="Cari NIM, nama, jurusan, atau fakultas"
                   value="{{ keyword }}">
            <button class="btn btn-success" type="submit">Cari</button>
            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Tampil Semua</a>
        </div>
    </form>

    <div class="mb-3">
        <a href="{{ url_for('cetak_pdf', keyword=keyword) }}" class="btn btn-danger btn-sm">Cetak PDF</a>
        <a href="{{ url_for('cetak_excel', keyword=keyword) }}" class="btn btn-success btn-sm">Cetak Excel</a>
        <a href="{{ url_for('cetak_csv', keyword=keyword) }}" class="btn btn-info btn-sm">Cetak CSV</a>
    </div>

    <div class="card mb-3">
        <div class="card-header bg-dark text-white">Daftar Mahasiswa</div>
        <div class="card-body table-responsive">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>No</th>
                        <th>NIM</th>
                        <th>Nama</th>
                        <th>Jurusan</th>
                        <th>Fakultas</th>
                        <th width="160">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in data %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ row.nim }}</td>
                        <td>{{ row.nama }}</td>
                        <td>{{ row.jurusan }}</td>
                        <td>{{ row.fakultas }}</td>
                        <td>
                            <a href="{{ url_for('edit', nim=row.nim) }}" class="btn btn-warning btn-sm">Edit</a>
                            <a href="{{ url_for('hapus', nim=row.nim) }}" class="btn btn-danger btn-sm" onclick="return confirm('Yakin ingin menghapus data mahasiswa ini?')">Hapus</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center">Data mahasiswa belum tersedia</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>
"""


# ============================================================
# TEMPLATE HTML EDIT
# ============================================================

HTML_EDIT = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit Mahasiswa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4">
    <h3>Edit Data Mahasiswa</h3>

    <div class="alert alert-warning">
        Data mahasiswa diperbarui berdasarkan NIM lama: {{ old.nim }}.
    </div>

    <div class="card">
        <div class="card-header bg-warning">Form Edit Mahasiswa</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('update', old_nim=old.nim) }}">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>NIM</label>
                        <input type="number" name="nim" value="{{ data.nim }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Nama</label>
                        <input type="text" name="nama" value="{{ data.nama }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Jurusan</label>
                        <input type="text" name="jurusan" value="{{ data.jurusan }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Fakultas</label>
                        <input type="text" name="fakultas" value="{{ data.fakultas }}"
                               class="form-control" required>
                    </div>
                </div>

                <button type="submit" class="btn btn-primary">Update</button>
                <a href="{{ url_for('index') }}" class="btn btn-secondary">Kembali</a>
            </form>
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
    keyword = request.args.get("keyword", "")
    data = ambil_mahasiswa(keyword)
    return render_template_string(
        HTML_INDEX,
        data=data,
        keyword=keyword,
    )


@app.route("/cetak_csv")
def cetak_csv():
    keyword = request.args.get("keyword", "")
    rows = ambil_mahasiswa(keyword)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(KOLOM_CETAK)

    for row in rows:
        writer.writerow(format_data_row(row))

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=laporan_mahasiswa.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@app.route("/cetak_excel")
def cetak_excel():
    keyword = request.args.get("keyword", "")
    rows = ambil_mahasiswa(keyword)

    html = """
    <html>
    <head><meta charset='utf-8'></head>
    <body>
    <h3>Laporan Data Mahasiswa</h3>
    <table border='1'>
        <tr>
    """

    for kolom in KOLOM_CETAK:
        html += "<th>" + escape(str(kolom)) + "</th>"

    html += "</tr>"

    for row in rows:
        html += "<tr>"
        for item in format_data_row(row):
            html += "<td>" + escape(str(item)) + "</td>"
        html += "</tr>"

    html += """
        <tr>
            <td colspan='3'><b>Total</b></td>
            <td><b>{}</b></td>
        </tr>
    </table>
    </body>
    </html>
    """.format(len(rows))

    response = make_response(html)
    response.headers["Content-Disposition"] = "attachment; filename=laporan_mahasiswa.xls"
    response.headers["Content-Type"] = "application/vnd.ms-excel; charset=utf-8"
    return response


@app.route("/cetak_pdf")
def cetak_pdf():
    keyword = request.args.get("keyword", "")
    rows = ambil_mahasiswa(keyword)
    pdf_data = buat_pdf_sederhana(rows)

    response = make_response(pdf_data)
    response.headers["Content-Disposition"] = "attachment; filename=laporan_mahasiswa.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response


@app.route("/simpan", methods=["POST"])
def simpan():
    try:
        nim = int(request.form["nim"])
    except ValueError:
        flash("NIM harus berupa angka")
        return redirect(url_for("index"))

    nama = request.form["nama"].strip()
    jurusan = request.form["jurusan"].strip()
    fakultas = request.form["fakultas"].strip()

    if not nama:
        flash("Nama tidak boleh kosong")
        return redirect(url_for("index"))
    if not jurusan:
        flash("Jurusan tidak boleh kosong")
        return redirect(url_for("index"))
    if not fakultas:
        flash("Fakultas tidak boleh kosong")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO mahasiswa (nim, nama, jurusan, fakultas)
            VALUES (%s, %s, %s, %s)
            """,
            (nim, nama, jurusan, fakultas),
        )
        conn.commit()
        flash("Data mahasiswa berhasil disimpan")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data mahasiswa gagal disimpan. NIM sudah ada")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:nim>")
def edit(nim):
    data = ambil_mahasiswa_by_nim(nim)
    if data is None:
        flash("Data mahasiswa tidak ditemukan")
        return redirect(url_for("index"))

    old = {"nim": nim}
    return render_template_string(
        HTML_EDIT,
        data=data,
        old=old,
    )


@app.route("/update/<int:old_nim>", methods=["POST"])
def update(old_nim):
    try:
        nim = int(request.form["nim"])
    except ValueError:
        flash("NIM harus berupa angka")
        return redirect(url_for("index"))

    nama = request.form["nama"].strip()
    jurusan = request.form["jurusan"].strip()
    fakultas = request.form["fakultas"].strip()

    if not nama:
        flash("Nama tidak boleh kosong")
        return redirect(url_for("index"))
    if not jurusan:
        flash("Jurusan tidak boleh kosong")
        return redirect(url_for("index"))
    if not fakultas:
        flash("Fakultas tidak boleh kosong")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE mahasiswa
            SET nim = %s,
                nama = %s,
                jurusan = %s,
                fakultas = %s
            WHERE nim = %s
            """,
            (nim, nama, jurusan, fakultas, old_nim),
        )
        conn.commit()
        flash("Data mahasiswa berhasil diupdate")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data mahasiswa gagal diupdate. NIM sudah ada")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/hapus/<int:nim>")
def hapus(nim):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM mahasiswa
        WHERE nim = %s
        """,
        (nim,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Data mahasiswa berhasil dihapus")
    return redirect(url_for("index"))


# ============================================================
# PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":
    buat_tabel()
    app.run(debug=True, port=5003)
