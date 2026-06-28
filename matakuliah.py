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
        CREATE TABLE IF NOT EXISTS matakuliah (
            kodemk VARCHAR(20) PRIMARY KEY,
            namamk VARCHAR(100),
            sks INT,
            biaya DECIMAL(12,2)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def ambil_matakuliah(keyword=""):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT kodemk, namamk, sks, biaya
        FROM matakuliah
    """
    params = []

    if keyword:
        keyword_like = f"%{keyword}%"
        query += """
            WHERE kodemk LIKE %s
               OR namamk LIKE %s
               OR CAST(sks AS CHAR) LIKE %s
               OR CAST(biaya AS CHAR) LIKE %s
        """
        params = [keyword_like] * 4

    query += " ORDER BY kodemk"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def ambil_matakuliah_by_kodemk(kodemk):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT kodemk, namamk, sks, biaya
        FROM matakuliah
        WHERE kodemk = %s
        """,
        (kodemk,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def cek_matakuliah_referensi(kodemk):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS jumlah
        FROM krs
        WHERE kodemk = %s
        """,
        (kodemk,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["jumlah"] if result else 0


# ============================================================
# Utility/helper functions
# ============================================================

KOLOM_CETAK = [
    "Kode MK", "Nama MK", "SKS", "Biaya"
]


def format_data_row(row):
    return [
        row["kodemk"],
        row["namamk"],
        row["sks"],
        row["biaya"],
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
        "LAPORAN DATA MATAKULIAH",
        "",
        format_baris(KOLOM_CETAK),
        "-" * 170,
    ]

    for row in rows:
        isi_baris.append(format_baris(format_data_row(row)))

    isi_baris += ["-" * 170, f"Total Mata Kuliah: {len(rows)}"]

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
    <title>Form Data Mata Kuliah</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4 mb-5">
    <h3>Form Data Mata Kuliah - Flask dan MySQL</h3>
    <p class="text-muted">
        CRUD tabel Matakuliah menggunakan primary key Kode MK.
    </p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="card mb-3">
        <div class="card-header bg-primary text-white">Input Data Mata Kuliah</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('simpan') }}">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>Kode MK</label>
                        <input type="text" name="kodemk" class="form-control"
                               placeholder="MK001" required>
                    </div>
                    <div class="col-md-4 mb-2">
                        <label>Nama Mata Kuliah</label>
                        <input type="text" name="namamk" class="form-control"
                               placeholder="Nama Mata Kuliah" required>
                    </div>
                    <div class="col-md-2 mb-2">
                        <label>SKS</label>
                        <input type="number" name="sks" class="form-control"
                               placeholder="3" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Biaya</label>
                        <input type="text" name="biaya" class="form-control"
                               placeholder="350000" required>
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
                   placeholder="Cari Kode MK, nama MK, SKS, atau biaya"
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
        <div class="card-header bg-dark text-white">Daftar Mata Kuliah</div>
        <div class="card-body table-responsive">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>No</th>
                        <th>Kode MK</th>
                        <th>Nama Mata Kuliah</th>
                        <th>SKS</th>
                        <th>Biaya</th>
                        <th width="160">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in data %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ row.kodemk }}</td>
                        <td>{{ row.namamk }}</td>
                        <td>{{ row.sks }}</td>
                        <td>Rp {{ "{:,.0f}".format(row.biaya or 0) }}</td>
                        <td>
                            <a href="{{ url_for('edit', kodemk=row.kodemk) }}" class="btn btn-warning btn-sm">Edit</a>
                            <a href="{{ url_for('hapus', kodemk=row.kodemk) }}" class="btn btn-danger btn-sm" onclick="return confirm('Yakin ingin menghapus matakuliah ini?')">Hapus</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center">Data mata kuliah belum tersedia</td>
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
    <title>Edit Mata Kuliah</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4">
    <h3>Edit Data Mata Kuliah</h3>

    <div class="alert alert-warning">
        Data matakuliah diperbarui berdasarkan kode MK lama: {{ old.kodemk }}.
    </div>

    <div class="card">
        <div class="card-header bg-warning">Form Edit Mata Kuliah</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('update', old_kodemk=old.kodemk) }}">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>Kode MK</label>
                        <input type="text" name="kodemk" value="{{ data.kodemk }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-4 mb-2">
                        <label>Nama Mata Kuliah</label>
                        <input type="text" name="namamk" value="{{ data.namamk }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-2 mb-2">
                        <label>SKS</label>
                        <input type="number" name="sks" value="{{ data.sks }}"
                               class="form-control" required>
                    </div>
                    <div class="col-md-3 mb-2">
                        <label>Biaya</label>
                        <input type="text" name="biaya" value="{{ data.biaya }}"
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
    data = ambil_matakuliah(keyword)
    return render_template_string(
        HTML_INDEX,
        data=data,
        keyword=keyword,
    )


@app.route("/cetak_csv")
def cetak_csv():
    keyword = request.args.get("keyword", "")
    rows = ambil_matakuliah(keyword)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(KOLOM_CETAK)

    for row in rows:
        writer.writerow(format_data_row(row))

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=laporan_matakuliah.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@app.route("/cetak_excel")
def cetak_excel():
    keyword = request.args.get("keyword", "")
    rows = ambil_matakuliah(keyword)

    html = [
        "<html>",
        "<head><meta charset='utf-8'></head>",
        "<body>",
        "<h3>Laporan Data Mata Kuliah</h3>",
        "<table border='1'>",
        "<tr>",
    ]

    for kolom in KOLOM_CETAK:
        html.append(f"<th>{escape(str(kolom))}</th>")

    html.extend(["</tr>", "<tbody>"])

    for row in rows:
        html.append("<tr>")
        for item in format_data_row(row):
            html.append(f"<td>{escape(str(item))}</td>")
        html.append("</tr>")

    html.extend([
        "<tr>",
        "<td colspan='3'><b>Total</b></td>",
        f"<td><b>{len(rows)}</b></td>",
        "</tr>",
        "</tbody>",
        "</table>",
        "</body>",
        "</html>",
    ])

    response = make_response("".join(html))
    response.headers["Content-Disposition"] = "attachment; filename=laporan_matakuliah.xls"
    response.headers["Content-Type"] = "application/vnd.ms-excel; charset=utf-8"
    return response


@app.route("/cetak_pdf")
def cetak_pdf():
    keyword = request.args.get("keyword", "")
    rows = ambil_matakuliah(keyword)
    pdf_data = buat_pdf_sederhana(rows)

    response = make_response(pdf_data)
    response.headers["Content-Disposition"] = "attachment; filename=laporan_matakuliah.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response


@app.route("/simpan", methods=["POST"])
def simpan():
    kodemk = request.form["kodemk"].strip()
    namamk = request.form["namamk"].strip()
    try:
        sks = int(request.form["sks"])
    except ValueError:
        flash("SKS harus berupa angka")
        return redirect(url_for("index"))

    try:
        biaya = float(request.form["biaya"])
    except ValueError:
        flash("Biaya harus berupa angka")
        return redirect(url_for("index"))

    if not kodemk:
        flash("Kode MK tidak boleh kosong")
        return redirect(url_for("index"))
    if not namamk:
        flash("Nama Mata Kuliah tidak boleh kosong")
        return redirect(url_for("index"))
    if sks <= 0:
        flash("SKS harus lebih besar dari 0")
        return redirect(url_for("index"))
    if biaya < 0:
        flash("Biaya tidak boleh negatif")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO matakuliah (kodemk, namamk, sks, biaya)
            VALUES (%s, %s, %s, %s)
            """,
            (kodemk, namamk, sks, biaya),
        )
        conn.commit()
        flash("Data matakuliah berhasil disimpan")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data matakuliah gagal disimpan. Kode MK sudah ada")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<kodemk>")
def edit(kodemk):
    data = ambil_matakuliah_by_kodemk(kodemk)
    if data is None:
        flash("Data matakuliah tidak ditemukan")
        return redirect(url_for("index"))

    old = {"kodemk": kodemk}
    return render_template_string(
        HTML_EDIT,
        data=data,
        old=old,
    )


@app.route("/update/<old_kodemk>", methods=["POST"])
def update(old_kodemk):
    kodemk = request.form["kodemk"].strip()
    namamk = request.form["namamk"].strip()
    try:
        sks = int(request.form["sks"])
    except ValueError:
        flash("SKS harus berupa angka")
        return redirect(url_for("index"))

    try:
        biaya = float(request.form["biaya"])
    except ValueError:
        flash("Biaya harus berupa angka")
        return redirect(url_for("index"))

    if not kodemk:
        flash("Kode MK tidak boleh kosong")
        return redirect(url_for("index"))
    if not namamk:
        flash("Nama Mata Kuliah tidak boleh kosong")
        return redirect(url_for("index"))
    if sks <= 0:
        flash("SKS harus lebih besar dari 0")
        return redirect(url_for("index"))
    if biaya < 0:
        flash("Biaya tidak boleh negatif")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE matakuliah
            SET kodemk = %s,
                namamk = %s,
                sks = %s,
                biaya = %s
            WHERE kodemk = %s
            """,
            (kodemk, namamk, sks, biaya, old_kodemk),
        )
        conn.commit()
        flash("Data matakuliah berhasil diupdate")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data matakuliah gagal diupdate. Kode MK sudah ada")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/hapus/<kodemk>")
def hapus(kodemk):
    if cek_matakuliah_referensi(kodemk) > 0:
        flash("This course cannot be deleted because it is still referenced by KRS data.")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM matakuliah
        WHERE kodemk = %s
        """,
        (kodemk,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Data matakuliah berhasil dihapus")
    return redirect(url_for("index"))


# ============================================================
# PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":
    buat_tabel()
    app.run(debug=True, port=5004)
