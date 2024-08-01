import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'tasks.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       title TEXT NOT NULL,
                       description TEXT,
                       due_date TEXT)''')
    conn.commit()
    conn.close()

@app.route('/tasks', methods=['POST'])
def add_task():
    conn = get_db_connection()
    cursor = conn.cursor()
    data = request.get_json()
    cursor.execute('INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)',
                   (data['title'], data.get('description', ''), data.get('due_date', '')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task added successfully'})

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    conn.close()
    if task:
        return jsonify(dict(task))
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = request.get_json()
    cursor.execute('UPDATE tasks SET title = ?, description = ?, due_date = ? WHERE id = ?',
                   (data['title'], data.get('description', ''), data.get('due_date', ''), task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task updated successfully'})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task deleted successfully'})

@app.route('/tasks/due_date/<string:due_date>', methods=['GET'])
def get_tasks_by_due_date(due_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE due_date = ?', (due_date,))
    tasks = cursor.fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])

if __name__ == '__main__':
    create_table()
    app.run()