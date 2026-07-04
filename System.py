import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------------------------------------------
# 1. INITIALIZATION & CONFIGURATION
# -------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'super_secret_hackathon_key'
DATABASE = 'hrms.db'

# -------------------------------------------------------------
# 2. DATABASE SETUP & HELPER FUNCTIONS
# -------------------------------------------------------------
def get_db_connection():
    """Establishes a connection to the SQLite database and returns rows as dictionaries."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    """Creates the necessary tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users & Profiles combined for easy beginner implementation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('Employee', 'HR_Admin')) NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            designation TEXT,
            base_salary REAL DEFAULT 30000.0,
            leave_balance INTEGER DEFAULT 15
        )
    ''')
    
    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT CHECK(status IN ('Present', 'Absent', 'Half-day', 'Leave')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, work_date)
        )
    ''')
    
    # Leave Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type TEXT CHECK(leave_type IN ('Paid', 'Sick', 'Unpaid')) NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            remarks TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# 3. HTML TEMPLATES (Embedded raw strings for single-file setup)
# -------------------------------------------------------------
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HRMS - Hackathon Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-800 font-sans">
    <nav class="bg-indigo-600 p-4 text-white flex justify-between items-center shadow-md">
        <a href="/" class="text-xl font-bold tracking-wider">⚡ Odoo x Adamas HRMS</a>
        <div>
            {% if session.get('user_id') %}
                <span class="mr-4 text-indigo-200">Logged in as: <strong>{{ session['role'] }}</strong></span>
                <a href="/logout" class="bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded transition">Logout</a>
            {% else %}
                <a href="/login" class="hover:underline mr-4">Login</a>
                <a href="/register" class="bg-white text-indigo-600 px-3 py-1.5 rounded font-medium shadow">Register</a>
            {% endif %}
        </div>
    </nav>
    <div class="max-w-6xl mx-auto mt-8 p-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, msg in messages %}
                    <div class="p-4 mb-4 rounded {% if category=='error' %}bg-red-100 text-red-700{% else %}bg-green-100 text-green-700{% endif %}">
                        {{ msg }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-100">
    <h2 class="text-2xl font-bold mb-6 text-center text-indigo-600">Account Sign In</h2>
    <form method="POST">
        <div class="mb-4">
            <label class="block text-sm font-semibold mb-1">Email Address</label>
            <input type="email" name="email" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <div class="mb-6">
            <label class="block text-sm font-semibold mb-1">Password</label>
            <input type="password" name="password" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white p-2.5 rounded font-medium transition">Login</button>
    </form>
</div>
{% endblock %}
"""

REGISTER_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-100">
    <h2 class="text-2xl font-bold mb-6 text-center text-indigo-600">Employee Registration</h2>
    <form method="POST">
        <div class="mb-4">
            <label class="block text-sm font-semibold mb-1">Employee ID</label>
            <input type="text" name="employee_id" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <div class="mb-4">
            <label class="block text-sm font-semibold mb-1">Full Name</label>
            <input type="text" name="full_name" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <div class="mb-4">
            <label class="block text-sm font-semibold mb-1">Email Address</label>
            <input type="email" name="email" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <div class="mb-4">
            <label class="block text-sm font-semibold mb-1">Password</label>
            <input type="password" name="password" required class="w-full border p-2 rounded focus:outline-indigo-500">
        </div>
        <div class="mb-6">
            <label class="block text-sm font-semibold mb-1">System Account Role</label>
            <select name="role" class="w-full border p-2 rounded focus:outline-indigo-500 bg-white">
                <option value="Employee">Regular Employee</option>
                <option value="HR_Admin">HR Administrator</option>
            </select>
        </div>
        <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white p-2.5 rounded font-medium transition">Create Account</button>
    </form>
</div>
{% endblock %}
"""

DASHBOARD_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-extrabold text-gray-900">Welcome back, {{ user['full_name'] }}!</h1>
    <p class="text-gray-500">Role: {{ user['role'] }} | Title: {{ user['designation'] or 'Not Assigned' }}</p>
</div>

{% if user['role'] == 'Employee' %}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 class="text-sm uppercase tracking-wide text-gray-400 font-bold mb-1">Available Vacation Days</h3>
            <p class="text-3xl font-black text-indigo-600">{{ user['leave_balance'] }} Days</p>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 class="text-sm uppercase tracking-wide text-gray-400 font-bold mb-1">Base Monthly Payroll</h3>
            <p class="text-3xl font-black text-emerald-600">₹{{ user['base_salary'] }}</p>
        </div>
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col justify-between">
            <h3 class="text-sm uppercase tracking-wide text-gray-400 font-bold mb-2">Daily Attendance Logs</h3>
            <form action="/check-in-out" method="POST" class="flex gap-2">
                <button name="action" value="check_in" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded font-medium text-sm transition">Check In</button>
                <button name="action" value="check_out" class="flex-1 bg-gray-800 hover:bg-gray-900 text-white py-2 rounded font-medium text-sm transition">Check Out</button>
            </form>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Apply for Absence Time-Off</h2>
            <form action="/apply-leave" method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Leave Type</label>
                    <select name="leave_type" class="w-full border p-2 rounded bg-white">
                        <option value="Paid">Paid Leave</option>
                        <option value="Sick">Sick Leave</option>
                        <option value="Unpaid">Unpaid Leave</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Start Date</label>
                        <input type="date" name="start_date" required class="w-full border p-2 rounded">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">End Date</label>
                        <input type="date" name="end_date" required class="w-full border p-2 rounded">
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Reason / Notes</label>
                    <textarea name="remarks" rows="2" class="w-full border p-2 rounded"></textarea>
                </div>
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded font-medium transition">Submit Request</button>
            </form>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Your Recent Activity Log</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-gray-400 border-b">
                            <th class="py-2">Date</th>
                            <th class="py-2">Check In</th>
                            <th class="py-2">Check Out</th>
                            <th class="py-2">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y">
                        {% for log in attendance_logs %}
                        <tr>
                            <td class="py-2 font-medium">{{ log['work_date'] }}</td>
                            <td class="py-2 text-gray-500">{{ log['check_in'] or '--:--' }}</td>
                            <td class="py-2 text-gray-500">{{ log['check_out'] or '--:--' }}</td>
                            <td class="py-2"><span class="px-2 py-0.5 rounded text-xs bg-green-100 text-green-800 font-bold">{{ log['status'] }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

{% else %}
    <div class="grid grid-cols-1 gap-8">
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-4 text-indigo-600 border-b pb-2">Pending Global Absence Clearances</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-gray-400 border-b">
                            <th class="py-2">Employee</th>
                            <th class="py-2">Type</th>
                            <th class="py-2">Duration</th>
                            <th class="py-2">Reason Provided</th>
                            <th class="py-2">Current Status</th>
                            <th class="py-2 text-right">Administrative Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y">
                        {% for req in leave_requests %}
                        <tr>
                            <td class="py-3 font-semibold text-gray-900">{{ req['full_name'] }}</td>
                            <td class="py-3 text-gray-600">{{ req['leave_type'] }}</td>
                            <td class="py-3 text-gray-500">{{ req['start_date'] }} to {{ req['end_date'] }}</td>
                            <td class="py-3 text-gray-500 italic">"{{ req['remarks'] }}"</td>
                            <td class="py-3"><span class="px-2 py-1 rounded text-xs font-bold bg-amber-100 text-amber-800">{{ req['status'] }}</span></td>
                            <td class="py-3 text-right space-x-1">
                                <a href="/admin/leave/{{ req['id'] }}/Approved" class="bg-emerald-500 hover:bg-emerald-600 text-white px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition">Approve</a>
                                <a href="/admin/leave/{{ req['id'] }}/Rejected" class="bg-rose-500 hover:bg-rose-600 text-white px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition">Reject</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Active Corporate Roster & Payroll Directory</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-gray-400 border-b">
                            <th class="py-2">ID</th>
                            <th class="py-2">Name</th>
                            <th class="py-2">Role</th>
                            <th class="py-2">Base Salary</th>
                            <th class="py-2">Leave Bal.</th>
                            <th class="py-2 text-right">Quick Base Adjust</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y">
                        {% for emp in employee_list %}
                        <tr>
                            <td class="py-3 text-gray-500 font-mono">{{ emp['employee_id'] }}</td>
                            <td class="py-3 font-bold text-gray-900">{{ emp['full_name'] }}</td>
                            <td class="py-3 text-gray-600">{{ emp['role'] }}</td>
                            <td class="py-3 text-emerald-600 font-semibold">₹{{ emp['base_salary'] }}</td>
                            <td class="py-3 font-medium">{{ emp['leave_balance'] }} Days</td>
                            <td class="py-3 text-right">
                                <form action="/admin/update-salary/{{ emp['id'] }}" method="POST" class="inline-flex gap-1 justify-end">
                                    <input type="number" name="new_salary" value="{{ emp['base_salary'] }}" class="w-24 text-xs border p-1 rounded font-semibold text-center">
                                    <button type="submit" class="bg-indigo-600 text-white px-2 py-1 rounded text-xs hover:bg-indigo-700 transition">Save</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
{% endif %}
{% endblock %}
"""

# Injection logic mapping to solve the missing TemplateNotFound issue dynamically
# This binds our BASE_LAYOUT string string to the name 'base' inside Flask's view template loader engine
from jinja2 import DictLoader
app.jinja_loader = DictLoader({'base': BASE_LAYOUT})

# -------------------------------------------------------------
# 4. CONTROLLER LAYER (Routes & System Business Logic)
# -------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    attendance_logs = []
    leave_requests = []
    employee_list = []
    
    if user['role'] == 'Employee':
        attendance_logs = conn.execute('SELECT * FROM attendance WHERE user_id = ? ORDER BY work_date DESC', (user['id'],)).fetchall()
    else:
        leave_requests = conn.execute('''
            SELECT lr.*, u.full_name FROM leave_requests lr 
            JOIN users u ON lr.user_id = u.id 
            WHERE lr.status = 'Pending'
        ''').fetchall()
        employee_list = conn.execute('SELECT * FROM users').fetchall()
        
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, user=user, attendance_logs=attendance_logs, leave_requests=leave_requests, employee_list=employee_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        emp_id = request.form['employee_id']
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (employee_id, full_name, email, password, role) VALUES (?, ?, ?, ?, ?)',
                (emp_id, full_name, email, hashed_pw, role)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Error: Employee ID or Email address already registered.', 'error')
        finally:
            conn.close()
            
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash('Welcome to your command dashboard.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid login authentication credentials matching.', 'error')
            
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully securely logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/check-in-out', methods=['POST'])
def check_in_out():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    action = request.form.get('action')
    today_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H:%M:%S')
    
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND work_date = ?', (session['user_id'], today_str)).fetchone()
    
    if action == 'check_in':
        if not existing:
            conn.execute('INSERT INTO attendance (user_id, work_date, check_in, status) VALUES (?, ?, ?, ?)', (session['user_id'], today_str, time_str, 'Present'))
            flash('Successfully checked in for today!', 'success')
        else:
            flash('You have already logged a check-in timestamp for today.', 'error')
    elif action == 'check_out':
        if existing and not existing['check_out']:
            conn.execute('UPDATE attendance SET check_out = ? WHERE id = ?', (time_str, existing['id']))
            flash('Successfully clocked out. Have a great evening!', 'success')
        else:
            flash('Cannot process clock-out. Ensure check-in exists and you haven\'t clocked out already.', 'error')
            
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/apply-leave', methods=['POST'])
def apply_leave():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    leave_type = request.form['leave_type']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    remarks = request.form['remarks']
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, remarks) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], leave_type, start_date, end_date, remarks)
    )
    conn.commit()
    conn.close()
    flash('Absence tracking request submitted successfully to the HR approval queue.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/leave/<int:request_id>/<string:new_status>')
def process_leave(request_id, new_status):
    if session.get('role') != 'HR_Admin': 
        return "Unauthorized Access", 403
        
    conn = get_db_connection()
    leave_req = conn.execute('SELECT * FROM leave_requests WHERE id = ?', (request_id,)).fetchone()
    
    if leave_req and new_status == 'Approved' and leave_req['leave_type'] != 'Unpaid':
        conn.execute('UPDATE users SET leave_balance = MAX(0, leave_balance - 1) WHERE id = ?', (leave_req['user_id'],))
        
    conn.execute('UPDATE leave_requests SET status = ? WHERE id = ?', (new_status, request_id))
    conn.commit()
    conn.close()
    flash(f'Leave request explicitly updated to: {new_status}', 'success')
    return redirect(url_for('index'))

@app.route('/admin/update-salary/<int:emp_id>', methods=['POST'])
def update_salary(emp_id):
    if session.get('role') != 'HR_Admin': 
        return "Unauthorized Access", 403
        
    new_salary = request.form['new_salary']
    conn = get_db_connection()
    conn.execute('UPDATE users SET base_salary = ? WHERE id = ?', (new_salary, emp_id))
    conn.commit()
    conn.close()
    flash('Employee baseline salary structure updated perfectly.', 'success')
    return redirect(url_for('index'))

# -------------------------------------------------------------
# 5. EXECUTION BOOTSTRAPPING ENGINE
# -------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)