import os
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash


class DBConnection:
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()

    def cursor(self):
        return self._cursor

    def execute(self, query, params=None):
        if params is None:
            self._cursor.execute(query)
        else:
            self._cursor.execute(query, params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def commit(self):
        self._conn.commit()

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass
        self._conn.close()


def get_db_connection():
    connection_url = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('SUPABASE_DATABASE_URL')
    )
    if not connection_url:
        raise RuntimeError(
            "DATABASE_URL belum diset. Tambahkan env var DATABASE_URL di Vercel "
            "dengan connection string Supabase Postgres (gunakan mode Connection "
            "Pooling/port 6543, bukan direct connection port 5432)."
        )

    if 'sslmode=' not in connection_url:
        connector = '&' if '?' in connection_url else '?'
        connection_url = f"{connection_url}{connector}sslmode=require"

    conn = psycopg2.connect(connection_url, cursor_factory=DictCursor)
    return DBConnection(conn)


def init_db():
    """Inisialisasi database Postgres dan membuat tabel yang diperlukan jika belum ada.

    Aman dipanggil berkali-kali (pakai IF NOT EXISTS), jadi bisa dijalankan
    setiap cold start di Vercel tanpa merusak data yang sudah ada.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fasilitas (
            id SERIAL PRIMARY KEY,
            nama TEXT NOT NULL,
            lokasi TEXT NOT NULL,
            deskripsi TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pengaduan (
            id SERIAL PRIMARY KEY,
            fasilitas_id INTEGER NOT NULL REFERENCES fasilitas(id),
            nama_pelapor TEXT NOT NULL,
            email TEXT NOT NULL,
            deskripsi TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Baru',
            catatan_admin TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        default_username = os.environ.get("DEFAULT_ADMIN_USERNAME", "Syadza Haifa")
        default_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "SyadzaHaifa11")
        pw_hash = generate_password_hash(default_password)
        cur.execute(
            "INSERT INTO admin (username, password_hash) VALUES (%s, %s)",
            (default_username, pw_hash),
        )

    conn.commit()
    conn.close()
