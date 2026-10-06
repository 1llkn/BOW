import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
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
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบแจ้งรับและนัดรับพัสดุหอพักนักศึกษา</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap" rel="stylesheet">
    <style> body { font-family: 'Kanit', sans-serif; } </style>
</head>
<body class="bg-slate-100 min-h-screen pb-10">

    <!-- Header -->
    <header class="bg-slate-800 text-white py-6 shadow-md text-center">
        <h1 class="text-2xl md:text-3xl font-bold">📦 ระบบแจ้งรับและนัดรับพัสดุหอพักนักศึกษา</h1>
        <p class="text-sky-400 text-sm mt-1 italic">จัดทำโดย ศักย์ศรณ์ แก่นจันทร์</p>
    </header>

    <main class="max-w-6xl mx-auto px-4 mt-6">
        
        <!-- Form Section -->
        <div class="bg-white p-6 rounded-xl shadow-sm mb-6 border border-slate-200">
            <h2 class="text-lg font-bold text-slate-700 mb-4 pb-2 border-b">📌 บันทึกพัสดุเข้าหอพัก</h2>
            <form id="addForm" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div class="lg:col-span-2">
                    <label class="block text-xs font-semibold text-slate-600 mb-1">เลขพัสดุ (Tracking No.)</label>
                    <input type="text" id="tracking" required class="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-sky-500 outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">เลขห้องพัก</label>
                    <input type="text" id="room" required class="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-sky-500 outline-none">
                </div>
                <div class="lg:col-span-2">
                    <label class="block text-xs font-semibold text-slate-600 mb-1">ชื่อ-นามสกุล นักศึกษา</label>
                    <input type="text" id="name" required class="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-sky-500 outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">บริษัทขนส่ง</label>
                    <select id="carrier" class="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-sky-500 outline-none">
                        <option value="Flash Express">Flash Express</option>
                        <option value="ไปรษณีย์ไทย">ไปรษณีย์ไทย</option>
                        <option value="Kerry Express">Kerry Express</option>
                        <option value="J&T Express">J&T Express</option>
                        <option value="Shopee Express">Shopee Express</option>
                        <option value="อื่น ๆ">อื่น ๆ</option>
                    </select>
                </div>
                <div class="lg:col-span-6 text-right mt-2">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2 rounded-lg text-sm transition">➕ บันทึกพัสดุ</button>
                </div>
            </form>
        </div>

        <!-- Action & Search Bar -->
        <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-4">
            <div class="flex w-full md:w-auto gap-2">
                <input type="text" id="searchInput" placeholder="🔍 ค้นหา (เลขห้อง / เลขพัสดุ)" class="border rounded-lg p-2 text-sm w-full md:w-64 focus:ring-2 focus:ring-sky-500 outline-none">
                <button onclick="loadPackages()" class="bg-sky-500 hover:bg-sky-600 text-white px-4 py-2 rounded-lg text-sm transition">ค้นหา</button>
                <button onclick="clearSearch()" class="bg-slate-500 hover:bg-slate-600 text-white px-3 py-2 rounded-lg text-sm transition">ล้าง</button>
            </div>
        </div>

        <!-- Table View -->
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
            <table class="w-full text-left text-sm border-collapse">
                <thead class="bg-slate-800 text-white text-xs uppercase">
                    <tr>
                        <th class="p-3 text-center">ID</th>
                        <th class="p-3">เลขพัสดุ</th>
                        <th class="p-3 text-center">ห้อง</th>
                        <th class="p-3">ชื่อนักศึกษา</th>
                        <th class="p-3 text-center">ขนส่ง</th>
                        <th class="p-3 text-center">วันที่บันทึก</th>
                        <th class="p-3 text-center">เวลานัดรับ</th>
                        <th class="p-3 text-center">สถานะ</th>
                        <th class="p-3 text-center">จัดการ</th>
                    </tr>
                </thead>
                <tbody id="packageTable" class="divide-y divide-slate-100">
                    <!-- Data rows loaded here -->
                </tbody>
            </table>
        </div>
    </main>

    <script>
        async function loadPackages() {
            initDB();
            const q = document.getElementById('searchInput').value;
            const res = await fetch(`/api/packages${q ? '?search=' + encodeURIComponent(q) : ''}`);
            const data = await res.json();
            
            const tbody = document.getElementById('packageTable');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-slate-400">ไม่พบข้อมูลพัสดุ</td></tr>`;
                return;
            }

            data.forEach(item => {
                let badgeClass = "bg-amber-100 text-amber-800";
                if(item.status === "นัดรับแล้ว") badgeClass = "bg-sky-100 text-sky-800";
                if(item.status === "รับเรียบร้อย") badgeClass = "bg-emerald-100 text-emerald-800";

                tbody.innerHTML += `
                    <tr class="hover:bg-slate-50 transition">
                        <td class="p-3 text-center font-mono text-slate-500">${item.id}</td>
                        <td class="p-3 font-semibold text-slate-700">${item.tracking_no}</td>
                        <td class="p-3 text-center font-bold text-sky-600">${item.room_no}</td>
                        <td class="p-3">${item.student_name}</td>
                        <td class="p-3 text-center"><span class="bg-slate-100 px-2 py-1 rounded text-xs">${item.carrier}</span></td>
                        <td class="p-3 text-center text-xs text-slate-500">${item.date_added}</td>
                        <td class="p-3 text-center text-xs text-slate-600">${item.appointment_time}</td>
                        <td class="p-3 text-center">
                            <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${badgeClass}">${item.status}</span>
                        </td>
                        <td class="p-3 text-center space-x-1">
                            <button onclick="setAppointment(${item.id})" class="bg-amber-500 hover:bg-amber-600 text-white text-xs px-2 py-1 rounded transition">📅 นัดหมาย</button>
                            <button onclick="completePickup(${item.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-2 py-1 rounded transition">✅ รับแล้ว</button>
                            <button onclick="deletePackage(${item.id})" class="bg-rose-500 hover:bg-rose-600 text-white text-xs px-2 py-1 rounded transition">🗑️ ลบ</button>
                        </td>
                    </tr>
                `;
            });
        }

        async function initDB() {
            await fetch('/api/init');
        }

        document.getElementById('addForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const body = {
                tracking_no: document.getElementById('tracking').value,
                room_no: document.getElementById('room').value,
                student_name: document.getElementById('name').value,
                carrier: document.getElementById('carrier').value
            };

            await fetch('/api/packages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            document.getElementById('tracking').value = '';
            document.getElementById('room').value = '';
            document.getElementById('name').value = '';
            loadPackages();
        });

        async function setAppointment(id) {
            const timeStr = prompt("กรุณาระบุเวลานัดรับพัสดุ (เช่น วันนี้ 17:30 น.):");
            if (timeStr) {
                await fetch(`/api/packages/${id}/appointment`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ time: timeStr })
                });
                loadPackages();
            }
        }

        async function completePickup(id) {
            if (confirm("ยืนยันว่านักศึกษามารับพัสดุไปแล้วใช่หรือไม่?")) {
                await fetch(`/api/packages/${id}/complete`, { method: 'PUT' });
                loadPackages();
            }
        }

        async function deletePackage(id) {
            if (confirm("ต้องการลบรายการนี้หรือไม่?")) {
                await fetch(`/api/packages/${id}`, { method: 'DELETE' });
                loadPackages();
            }
        }

        function clearSearch() {
            document.getElementById('searchInput').value = '';
            loadPackages();
        }

        loadPackages();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/init')
def api_init():
    init_db()
    return jsonify({"status": "ok"})

@app.route('/api/packages', methods=['GET'])
def get_packages():
    conn, db_type = get_db()
    cursor = conn.cursor()
    search = request.args.get('search', '').strip()

    if search:
        kw = f"%{search}%"
        if db_type == "postgres":
            cursor.execute("SELECT * FROM packages WHERE room_no ILIKE %s OR tracking_no ILIKE %s ORDER BY id DESC", (kw, kw))
        else:
            cursor.execute("SELECT * FROM packages WHERE room_no LIKE ? OR tracking_no LIKE ? ORDER BY id DESC", (kw, kw))
    else:
        cursor.execute("SELECT * FROM packages ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        if db_type == "postgres":
            result.append(dict(r))
        else:
            result.append(dict(r))
    return jsonify(result)

@app.route('/api/packages', methods=['POST'])
def add_package():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    ph = "%s" if db_type == "postgres" else "?"
    cursor.execute(f'''
        INSERT INTO packages (tracking_no, room_no, student_name, carrier, date_added)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
    ''', (data['tracking_no'], data['room_no'], data['student_name'], data['carrier'], now))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/packages/<int:item_id>/appointment', methods=['PUT'])
def set_appointment(item_id):
    data = request.json
    conn, db_type = get_db()
    cursor = conn.cursor()
    ph = "%s" if db_type == "postgres" else "?"
    cursor.execute(f"UPDATE packages SET appointment_time = {ph}, status = 'นัดรับแล้ว' WHERE id = {ph}", (data['time'], item_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/packages/<int:item_id>/complete', methods=['PUT'])
def complete_pickup(item_id):
    conn, db_type = get_db()
    cursor = conn.cursor()
    ph = "%s" if db_type == "postgres" else "?"
    cursor.execute(f"UPDATE packages SET status = 'รับเรียบร้อย', appointment_time = 'รับแล้ว' WHERE id = {ph}", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/packages/<int:item_id>', methods=['DELETE'])
def delete_package(item_id):
    conn, db_type = get_db()
    cursor = conn.cursor()
    ph = "%s" if db_type == "postgres" else "?"
    cursor.execute(f"DELETE FROM packages WHERE id = {ph}", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)