from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('task_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    due_date TEXT NOT NULL
                )
            ''')

init_db()

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or not all(k in data for k in ('task_name', 'description', 'due_date')):
        return jsonify({"error": "Missing required fields"}), 400
    task_name = data['task_name']
    description = data['description']
    due_date = data['due_date']
    with get_db_connection() as conn:
        with conn:
            conn.execute(
                'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
                (task_name, description, due_date)
            )
    return jsonify({"message": "Task added successfully"}), 201

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        cur = conn.execute(
            'SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ?',
            (pattern, pattern)
        )
        rows = cur.fetchall()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks), 200

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No fields to update provided"}), 400
    fields = []
    values = []
    for field in ('task_name', 'description', 'due_date'):
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "No fields to update provided"}), 400
    set_clause = ', '.join(fields)
    values.append(task_id)
    with get_db_connection() as conn:
        with conn:
            conn.execute(
                f'UPDATE tasks SET {set_clause} WHERE id = ?',
                tuple(values)
            )
    return jsonify({"message": "Task updated successfully"}), 200

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with get_db_connection() as conn:
        with conn:
            conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    return jsonify({"message": "Task deleted successfully"}), 200

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    if not due_date:
        return jsonify({"error": "due_date parameter is required"}), 400
    with get_db_connection() as conn:
        cur = conn.execute('SELECT * FROM tasks WHERE due_date = ?', (due_date,))
        rows = cur.fetchall()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks), 200

if __name__ == '__main__':
    app.run(debug=False)