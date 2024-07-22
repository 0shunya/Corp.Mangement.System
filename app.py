import json
import os
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Shlok123'
socketio = SocketIO(app)

CHECK_IN_FILE = 'check_in_data.json'
TASKS_FILE = 'tasks_data.json'
ATTENDANCE_FILE = 'attendance_data.json'
CHAT_FILE = 'chat_data.json'
USERS_FILE = 'users_data.json'

def read_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} if file_path != CHAT_FILE else []
    return {} if file_path != CHAT_FILE else []

def write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, default=str)

check_in_data = read_json(CHECK_IN_FILE)
tasks_data = read_json(TASKS_FILE)
attendance_data = read_json(ATTENDANCE_FILE)
chat_data = read_json(CHAT_FILE)
users_data = read_json(USERS_FILE)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id and password:
            if user_id in users_data and users_data[user_id]['password'] == password:
                session['user_id'] = user_id
                return redirect(url_for('dashboard'))
            return 'Invalid credentials', 400
        return 'User ID and Password cannot be null', 400
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id and password:
            users_data[user_id] = {"password": password, "registered_at": datetime.now().isoformat()}
            write_json(USERS_FILE, users_data)
            return redirect(url_for('login'))
        return 'User ID and Password cannot be null', 400
    return render_template('register.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        if user_id == '100' and password == 'code100':
            session['user_id'] = user_id
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        return 'Invalid credentials', 400
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/attendance_report', methods=['GET'])
def admin_attendance_report():
    if 'user_id' in session and session.get('is_admin'):
        return jsonify(attendance_data), 200
    return jsonify({"error": "Unauthorized access"}), 403

@app.route('/admin/task_report', methods=['GET'])
def admin_task_report():
    if 'user_id' in session and session.get('is_admin'):
        return jsonify(tasks_data), 200
    return jsonify({"error": "Unauthorized access"}), 403

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/checkin', methods=['POST'])
def check_in():
    user_id = session.get('user_id')
    if user_id:
        check_in_time = datetime.now()
        check_in_data[user_id] = check_in_time.isoformat()
        write_json(CHECK_IN_FILE, check_in_data)
        return jsonify({"message": "Checked in"}), 200
    return jsonify({"error": "User ID cannot be null"}), 400

@app.route('/checkout', methods=['POST'])
def check_out():
    user_id = session.get('user_id')
    if user_id:
        check_out_time = datetime.now()
        if user_id in check_in_data:
            attendance_data[user_id] = {
                "check_in": check_in_data[user_id],
                "check_out": check_out_time.isoformat()
            }
            del check_in_data[user_id]
            write_json(CHECK_IN_FILE, check_in_data)
            write_json(ATTENDANCE_FILE, attendance_data)
            return jsonify({"message": "Checked out"}), 200
        return jsonify({"message": "User not checked in"}), 400
    return jsonify({"error": "User ID cannot be null"}), 400

@app.route('/task_completion_report', methods=['POST'])
def task_completion_report():
    user_id = session.get('user_id')
    if user_id:
        task_details = request.json.get('task_details')
        completion_time = datetime.now()
        if user_id not in tasks_data:
            tasks_data[user_id] = []
        tasks_data[user_id].append({"task": task_details, "time": completion_time.isoformat()})
        write_json(TASKS_FILE, tasks_data)
        return jsonify({"message": "Task recorded"}), 200
    return jsonify({"error": "User ID cannot be null"}), 400

@app.route('/attendance_report', methods=['GET'])
def attendance_report():
    return jsonify(attendance_data), 200

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', chat_data=chat_data, current_user=session['user_id'])

@app.route('/admin/chat')
def admin_chat():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return render_template('chat.html', chat_data=chat_data, current_user=session['user_id'])

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    user_id = session.get('user_id')
    if user_id:
        global chat_data
        chat_data = [msg for msg in chat_data if msg['user_id'] != user_id]
        write_json(CHAT_FILE, chat_data)
        return jsonify({"message": "Chat cleared", "user_id": user_id}), 200
    return jsonify({"error": "User ID cannot be null"}), 400

@socketio.on('message')
def handle_message(msg):
    user_id = session.get('user_id')
    if user_id:
        timestamp = datetime.now().isoformat()
        chat_data.append({"user_id": user_id, "message": msg, "time": timestamp})
        write_json(CHAT_FILE, chat_data)
        emit('message', {"user_id": user_id, "message": msg, "time": timestamp}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
