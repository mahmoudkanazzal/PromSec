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
                description TEXT,
                due_date TEXT
            )
        ''')
        conn.commit()

init_db()

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    task_name = data.get('task_name')
    description = data.get('description')
    due_date = data.get('due_date')
    if not task_name or not description or not due_date:
        abort(400, description='Missing required fields: task_name, description, due_date')
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
            (task_name, description, due_date)
        )
        conn.commit()
    return jsonify(message='Task added successfully'), 201

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    query = '''
        SELECT * FROM tasks
        WHERE task_name LIKE ? COLLATE NOCASE
           OR description LIKE ? COLLATE NOCASE
    '''
    with get_db_connection() as conn:
        rows = conn.execute(query, (pattern, pattern)).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    fields = {}
    for key in ('task_name', 'description', 'due_date'):
        if key in data:
            fields[key] = data[key]
    if not fields:
        abort(400, description='No fields to update provided')
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values())
    params.append(task_id)
    query = f'UPDATE tasks SET {set_clause} WHERE id=?'
    with get_db_connection() as conn:
        conn.execute(query, params)
        conn.commit()
    return jsonify(message='Task updated successfully'), 200

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
    return jsonify(message='Task deleted successfully'), 200

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    if not due_date:
        abort(400, description='due_date query parameter is required')
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM tasks WHERE due_date=?', (due_date,)).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)