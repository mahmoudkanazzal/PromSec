from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('task_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/add_task', methods=['POST'])
def add_task():
    if not request.is_json:
        abort(400, description='Missing or invalid JSON payload')
    data = request.get_json()
    required_fields = ['task_name', 'description', 'due_date']
    for field in required_fields:
        if field not in data:
            abort(400, description=f'Missing field: {field}')
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
            (data['task_name'], data['description'], data['due_date'])
        )
        conn.commit()
    return jsonify({"message": "Task added successfully"}), 201

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ?',
            (pattern, pattern)
        ).fetchall()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks), 200

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if not request.is_json:
        abort(400, description='Missing or invalid JSON payload')
    data = request.get_json()
    allowed_fields = ['task_name', 'description', 'due_date']
    fields_to_update = [field for field in allowed_fields if field in data]
    if not fields_to_update:
        abort(400, description='No fields provided for update')
    set_clause = ', '.join([f"{field}=?" for field in fields_to_update])
    values = [data[field] for field in fields_to_update]
    values.append(task_id)
    with get_db_connection() as conn:
        conn.execute(
            f'UPDATE tasks SET {set_clause} WHERE id = ?',
            values
        )
        conn.commit()
    return jsonify({"message": "Task updated successfully"}), 200

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
    return jsonify({"message": "Task deleted successfully"}), 200

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    if not due_date:
        abort(400, description='Missing due_date query parameter')
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM tasks WHERE due_date = ?',
            (due_date,)
        ).fetchall()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)