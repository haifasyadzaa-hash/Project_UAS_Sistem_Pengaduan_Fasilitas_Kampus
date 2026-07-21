import os
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash

def get_db_connection():
    """Membuat koneksi ke database Postgres Supabase via Environment Variable."""
    connection_url = os.environ.get('DATABASE_URL')
    
    conn = psycopg2.connect(connection_url, cursor_factory=DictCursor)
    return conn

def init_db():
    """Inisialisasi database Postgres dan membuat tabel yang diperlukan jika belum ada."""
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
    
    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        pw_hash = generate_password_hash("SyadzaHaifa11")
        cur.execute(
            "INSERT INTO admin (username, password_hash) VALUES (%s, %s)",
            ("Syadza Haifa", pw_hash),
        )
        
    conn.commit()
    cur.close()
    conn.close()
