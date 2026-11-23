import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('task_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date TEXT NOT NULL
        )''')

@app.before_first_request
def before_first():
    init_db()

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json(silent=True) or {}
    required = ['task_name', 'description', 'due_date']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO tasks (task_name, description, due_date) VALUES (?,?,?)',
                (data['task_name'], data['description'], data['due_date'])
            )
        return jsonify({"message": "Task added successfully"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                'SELECT * FROM tasks WHERE task_name LIKE ? COLLATE NOCASE OR description LIKE ? COLLATE NOCASE',
                (pattern, pattern)
            )
            rows = cur.fetchall()
            tasks = [dict(row) for row in rows]
        return jsonify(tasks), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    fields = {k: data[k] for k in ('task_name', 'description', 'due_date') if k in data}
    if not fields:
        return jsonify({"error": "No fields to update provided"}), 400
    set_clause = ', '.join([f"{k}=?" for k in fields])
    params = list(fields.values())
    params.append(task_id)
    try:
        with get_db_connection() as conn:
            conn.execute(f'UPDATE tasks SET {set_clause} WHERE id=?', params)
        return jsonify({"message": "Task updated successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        return jsonify({"message": "Task deleted successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    if not due_date:
        return jsonify({"error": "due_date parameter is required"}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT * FROM tasks WHERE due_date=?', (due_date,))
            rows = cur.fetchall()
            tasks = [dict(row) for row in rows]
        return jsonify(tasks), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)