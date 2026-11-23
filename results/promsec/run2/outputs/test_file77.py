import os
import re
import sqlite3
from typing import Any, Dict, List, Optional
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

DB_PATH = 'task_manager.db'

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
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

def validate_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ''

def validate_due_date(date_str: Any) -> bool:
    if not isinstance(date_str, str):
        return False
    return re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str) is not None

def validate_task_id(task_id: Any) -> bool:
    return isinstance(task_id, int) and task_id > 0

def task_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {'id': row['id'], 'task_name': row['task_name'], 'description': row['description'], 'due_date': row['due_date']}

@app.route('/add_task', methods=['POST'])
def add_task() -> Any:
    data = request.get_json(silent=True) or {}
    task_name = data.get('task_name')
    description = data.get('description')
    due_date = data.get('due_date')
    if not (validate_non_empty_string(task_name) and validate_non_empty_string(description) and validate_due_date(due_date)):
        return jsonify({'error': 'Invalid input'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
                (task_name.strip(), description.strip(), due_date)
            )
            conn.commit()
        return jsonify({'message': 'Task created'}), 201
    except Exception as e:
        print(f'Error in add_task: {e}')
        return jsonify({'error': 'Server error'}), 500

@app.route('/search_tasks', methods=['GET'])
def search_tasks() -> Any:
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM tasks
                WHERE LOWER(task_name) LIKE LOWER(?)
                OR LOWER(description) LIKE LOWER(?)
                ''',
                (pattern, pattern)
            ).fetchall()
        tasks = [task_to_dict(row) for row in rows]
        return jsonify(tasks), 200
    except Exception as e:
        print(f'Error in search_tasks: {e}')
        return jsonify({'error': 'Server error'}), 500

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id: int) -> Any:
    if not validate_task_id(task_id):
        return jsonify({'error': 'Invalid task ID'}), 400
    data = request.get_json(silent=True) or {}
    fields: List[str] = []
    values: List[Any] = []
    if 'task_name' in data:
        if not validate_non_empty_string(data['task_name']):
            return jsonify({'error': 'Invalid task_name'}), 400
        fields.append('task_name = ?')
        values.append(data['task_name'].strip())
    if 'description' in data:
        if not validate_non_empty_string(data['description']):
            return jsonify({'error': 'Invalid description'}), 400
        fields.append('description = ?')
        values.append(data['description'].strip())
    if 'due_date' in data:
        if not validate_due_date(data['due_date']):
            return jsonify({'error': 'Invalid due_date'}), 400
        fields.append('due_date = ?')
        values.append(data['due_date'])
    if not fields:
        return jsonify({'error': 'No valid fields to update'}), 400
    values.append(task_id)
    sql = f'UPDATE tasks SET {", ".join(fields)} WHERE id = ?'
    try:
        with get_db_connection() as conn:
            cur = conn.execute(sql, tuple(values))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
        return jsonify({'message': 'Task updated'}), 200
    except Exception as e:
        print(f'Error in update_task: {e}')
        return jsonify({'error': 'Server error'}), 500

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id: int) -> Any:
    if not validate_task_id(task_id):
        return jsonify({'error': 'Invalid task ID'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
        return jsonify({'message': 'Task deleted'}), 200
    except Exception as e:
        print(f'Error in delete_task: {e}')
        return jsonify({'error': 'Server error'}), 500

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date() -> Any:
    due_date = request.args.get('due_date', '')
    if not validate_due_date(due_date):
        return jsonify({'error': 'Invalid due_date'}), 400
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE due_date = ?',
                (due_date,)
            ).fetchall()
        tasks = [task_to_dict(row) for row in rows]
        return jsonify(tasks), 200
    except Exception as e:
        print(f'Error in get_tasks_by_due_date: {e}')
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False)