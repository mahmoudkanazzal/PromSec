import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'tasks.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_task', methods=['POST'])
def add_task():
    conn = create_connection()
    cursor = conn.cursor()
    
    task_name = request.json.get('task_name')
    description = request.json.get('description')
    due_date = request.json.get('due_date')
    
    cursor.execute("INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)", (task_name, description, due_date))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task added successfully'})

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    conn = create_connection()
    cursor = conn.cursor()
    
    keyword = request.args.get('keyword')
    
    cursor.execute("SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ?", ('%'+keyword+'%', '%'+keyword+'%'))
    tasks = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'tasks': tasks})

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    
    task_name = request.json.get('task_name')
    description = request.json.get('description')
    due_date = request.json.get('due_date')
    
    cursor.execute("UPDATE tasks SET task_name = ?, description = ?, due_date = ? WHERE id = ?", (task_name, description, due_date, task_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task updated successfully'})

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task deleted successfully'})

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    conn = create_connection()
    cursor = conn.cursor()
    
    due_date = request.args.get('due_date')
    
    cursor.execute("SELECT * FROM tasks WHERE due_date = ?", (due_date,))
    tasks = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'tasks': tasks})

if __name__ == '__main__':
    app.run()