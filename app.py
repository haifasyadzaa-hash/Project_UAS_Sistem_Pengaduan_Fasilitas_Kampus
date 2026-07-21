from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "ganti-dengan-secret-key-yang-lebih-aman"  # TODO: ganti saat deploy

STATUS_LIST = ["Baru", "Diproses", "Selesai", "Ditolak"]


# ---------------------------------------------------------------------------
# Decorator untuk proteksi halaman admin (harus login)
# ---------------------------------------------------------------------------
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Silakan login terlebih dahulu untuk mengakses halaman ini.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped_view


# ---------------------------------------------------------------------------
# SISI PUBLIK
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    daftar_fasilitas = conn.execute(
        "SELECT * FROM fasilitas ORDER BY nama ASC"
    ).fetchall()
    conn.close()
    return render_template("index.html", daftar_fasilitas=daftar_fasilitas)


@app.route("/pengaduan/tambah", methods=["POST"])
def tambah_pengaduan():
    fasilitas_id = request.form.get("fasilitas_id", "").strip()
    nama_pelapor = request.form.get("nama_pelapor", "").strip()
    email = request.form.get("email", "").strip()
    deskripsi = request.form.get("deskripsi", "").strip()

    errors = []
    if not fasilitas_id:
        errors.append("Fasilitas wajib dipilih.")
    if not nama_pelapor:
        errors.append("Nama pelapor wajib diisi.")
    if not email or "@" not in email or "." not in email:
        errors.append("Email tidak valid.")
    if not deskripsi or len(deskripsi) < 10:
        errors.append("Deskripsi pengaduan minimal 10 karakter.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        (fasilitas_id, nama_pelapor, email, deskripsi),
    )
    conn.commit()
    conn.close()

    flash("Pengaduan berhasil dikirim. Terima kasih atas laporan Anda!", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# AUTENTIKASI ADMIN
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return redirect(url_for("login"))

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin is None or not check_password_hash(admin["password_hash"], password):
            flash("Username atau password salah.", "danger")
            return redirect(url_for("login"))

        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]
        flash(f"Selamat datang kembali, {admin['username']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    flash("Anda telah berhasil logout.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# DASHBOARD ADMIN
# ---------------------------------------------------------------------------
@app.route("/admin/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()

    total_pengaduan = conn.execute("SELECT COUNT(*) AS c FROM pengaduan").fetchone()["c"]
    total_fasilitas = conn.execute("SELECT COUNT(*) AS c FROM fasilitas").fetchone()["c"]

    per_status = conn.execute(
    ).fetchall()

    status_counts = {s: 0 for s in STATUS_LIST}
    for row in per_status:
        status_counts[row["status"]] = row["jumlah"]

    pengaduan_terbaru = conn.execute(
    ).fetchall()

    fasilitas_terbanyak_diadukan = conn.execute(
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_pengaduan=total_pengaduan,
        total_fasilitas=total_fasilitas,
        status_counts=status_counts,
        pengaduan_terbaru=pengaduan_terbaru,
        fasilitas_terbanyak_diadukan=fasilitas_terbanyak_diadukan,
    )


# ---------------------------------------------------------------------------
# CRUD FASILITAS (Admin)
# ---------------------------------------------------------------------------
@app.route("/admin/fasilitas")
@login_required
def daftar_fasilitas():
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM fasilitas ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("fasilitas_list.html", daftar_fasilitas=data)


@app.route("/admin/fasilitas/tambah", methods=["GET", "POST"])
@login_required
def tambah_fasilitas():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        lokasi = request.form.get("lokasi", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()

        if not nama or not lokasi:
            flash("Nama dan lokasi fasilitas wajib diisi.", "danger")
            return render_template("fasilitas_form.html", mode="tambah", fasilitas=request.form)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO fasilitas (nama, lokasi, deskripsi) VALUES (?, ?, ?)",
            (nama, lokasi, deskripsi),
        )
        conn.commit()
        conn.close()
        flash("Fasilitas baru berhasil ditambahkan.", "success")
        return redirect(url_for("daftar_fasilitas"))

    return render_template("fasilitas_form.html", mode="tambah", fasilitas=None)


@app.route("/admin/fasilitas/edit/<int:fasilitas_id>", methods=["GET", "POST"])
@login_required
def edit_fasilitas(fasilitas_id):
    conn = get_db_connection()
    fasilitas = conn.execute(
        "SELECT * FROM fasilitas WHERE id = ?", (fasilitas_id,)
    ).fetchone()

    if fasilitas is None:
        conn.close()
        flash("Data fasilitas tidak ditemukan.", "danger")
        return redirect(url_for("daftar_fasilitas"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        lokasi = request.form.get("lokasi", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()

        if not nama or not lokasi:
            conn.close()
            flash("Nama dan lokasi fasilitas wajib diisi.", "danger")
            return render_template("fasilitas_form.html", mode="edit", fasilitas=fasilitas)

        conn.execute(
            "UPDATE fasilitas SET nama = ?, lokasi = ?, deskripsi = ? WHERE id = ?",
            (nama, lokasi, deskripsi, fasilitas_id),
        )
        conn.commit()
        conn.close()
        flash("Data fasilitas berhasil diperbarui.", "success")
        return redirect(url_for("daftar_fasilitas"))

    conn.close()
    return render_template("fasilitas_form.html", mode="edit", fasilitas=fasilitas)


@app.route("/admin/fasilitas/hapus/<int:fasilitas_id>", methods=["POST"])
@login_required
def hapus_fasilitas(fasilitas_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM fasilitas WHERE id = ?", (fasilitas_id,))
    conn.commit()
    conn.close()
    flash("Data fasilitas berhasil dihapus.", "success")
    return redirect(url_for("daftar_fasilitas"))


# ---------------------------------------------------------------------------
# CRUD PENGADUAN (Admin)
# ---------------------------------------------------------------------------
@app.route("/admin/pengaduan")
@login_required
def daftar_pengaduan():
    filter_status = request.args.get("status", "")
    conn = get_db_connection()

    query = """SELECT p.*, f.nama AS nama_fasilitas
               FROM pengaduan p JOIN fasilitas f ON p.fasilitas_id = f.id"""
    params = []
    if filter_status:
        query += " WHERE p.status = ?"
        params.append(filter_status)
    query += " ORDER BY p.id DESC"

    data = conn.execute(query, params).fetchall()
    conn.close()
    return render_template(
        "pengaduan_list.html",
        daftar_pengaduan=data,
        status_list=STATUS_LIST,
        filter_status=filter_status,
    )


@app.route("/admin/pengaduan/edit/<int:pengaduan_id>", methods=["GET", "POST"])
@login_required
def edit_pengaduan(pengaduan_id):
    conn = get_db_connection()
    pengaduan = conn.execute(
        (pengaduan_id,),
    ).fetchone()

    if pengaduan is None:
        conn.close()
        flash("Data pengaduan tidak ditemukan.", "danger")
        return redirect(url_for("daftar_pengaduan"))

    if request.method == "POST":
        status_baru = request.form.get("status", "").strip()
        catatan_admin = request.form.get("catatan_admin", "").strip()

        if status_baru not in STATUS_LIST:
            conn.close()
            flash("Status tidak valid.", "danger")
            return redirect(url_for("edit_pengaduan", pengaduan_id=pengaduan_id))

        conn.execute(
            "UPDATE pengaduan SET status = ? WHERE id = ?",
            (status_baru, pengaduan_id),
        )
        conn.commit()
        conn.close()
        flash("Status pengaduan berhasil diperbarui.", "success")
        return redirect(url_for("daftar_pengaduan"))

    conn.close()
    return render_template("pengaduan_form.html", pengaduan=pengaduan, status_list=STATUS_LIST)


@app.route("/admin/pengaduan/hapus/<int:pengaduan_id>", methods=["POST"])
@login_required
def hapus_pengaduan(pengaduan_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM pengaduan WHERE id = ?", (pengaduan_id,))
    conn.commit()
    conn.close()
    flash("Data pengaduan berhasil dihapus.", "success")
    return redirect(url_for("daftar_pengaduan"))


# ---------------------------------------------------------------------------
# LAPORAN / STATISTIK
# ---------------------------------------------------------------------------
@app.route("/admin/laporan")
@login_required
def laporan():
    conn = get_db_connection()

    per_status = conn.execute(
    ).fetchall()
    status_counts = {s: 0 for s in STATUS_LIST}
    for row in per_status:
        status_counts[row["status"]] = row["jumlah"]

    per_fasilitas = conn.execute(
    ).fetchall()

    conn.close()
    return render_template(
        "laporan.html",
        status_counts=status_counts,
        per_fasilitas=per_fasilitas,
    )


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
