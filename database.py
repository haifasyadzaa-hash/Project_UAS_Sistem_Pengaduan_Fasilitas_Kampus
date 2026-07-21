import os
import sqlite3
from werkzeug.security import generate_password_hash


DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database and create required tables."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fasilitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            lokasi TEXT NOT NULL,
            deskripsi TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pengaduan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fasilitas_id INTEGER NOT NULL,
            nama_pelapor TEXT NOT NULL,
            email TEXT NOT NULL,
            deskripsi TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Baru',
            catatan_admin TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(fasilitas_id) REFERENCES fasilitas(id)
        )
        """
    )

    cur.execute("SELECT COUNT(*) as c FROM admin")
    if cur.fetchone()[0] == 0:
        pw_hash = generate_password_hash("SyadzaHaifa11")
        cur.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
            ("Syadza Haifa", pw_hash),
        )

    conn.commit()
    conn.close()
