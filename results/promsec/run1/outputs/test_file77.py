import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

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
init_db()

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    required = ['task_name', 'description', 'due_date']
    for key in required:
        if key not in data or not isinstance(data[key], str):
            return jsonify({'error': f'Missing or invalid {key}'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
                (data['task_name'], data['description'], data['due_date'])
            )
        return jsonify({'message': 'Task added successfully'}), 201
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ?',
                (pattern, pattern)
            ).fetchall()
        tasks = [dict(row) for row in rows]
        return jsonify(tasks), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    fields = {}
    for key in ['task_name', 'description', 'due_date']:
        if key in data:
            if not isinstance(data[key], str):
                return jsonify({'error': f'Invalid {key}'}), 400
            fields[key] = data[key]
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values())
    values.append(task_id)
    try:
        with get_db_connection() as conn:
            cur = conn.execute(f'UPDATE tasks SET {set_clause} WHERE id=?', values)
            if cur.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
        return jsonify({'message': 'Task updated successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
        return jsonify({'message': 'Task deleted successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    if not due_date:
        return jsonify({'error': 'due_date parameter required'}), 400
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE due_date=?',
                (due_date,)
            ).fetchall()
        tasks = [dict(row) for row in rows]
        return jsonify(tasks), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    app.run(debug=False)