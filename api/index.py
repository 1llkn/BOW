import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

# ใช้ URL ของ Supabase ที่คุณให้มาเป็นค่าเริ่มต้น
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:Pattaratop9686@db.pdjzhwmrdixpgdehmstf.supabase.co:5432/postgres")

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # เพิ่ม sslmode='require' เพื่อให้เชื่อมต่อกับ Supabase ได้
        conn = psycopg2.connect(url, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
        return conn, "postgres"
    else:
        conn = sqlite3.connect("dorm_packages.db")
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def init_db():
    try:
        conn, db_type = get_db()
        cursor = conn.cursor()
        if db_type == "postgres":
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS packages (
                    id SERIAL PRIMARY KEY,
                    tracking_no TEXT NOT NULL,
                    room_no TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    carrier TEXT NOT NULL,
                    date_added TEXT NOT NULL,
                    appointment_time TEXT DEFAULT 'ยังไม่นัดหมาย',
                    status TEXT DEFAULT 'รอรับพัสดุ'
                );
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_no TEXT NOT NULL,
                    room_no TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    carrier TEXT NOT NULL,
                    date_added TEXT NOT NULL,
                    appointment_time TEXT DEFAULT 'ยังไม่นัดหมาย',
                    status TEXT DEFAULT 'รอรับพัสดุ'
                );
            ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Init DB Error:", e)

# HTML UI Template
HTML_TEMPLATE = """



    
    
    ระบบแจ้งรับและนัดรับพัสดุหอพักนักศึกษา