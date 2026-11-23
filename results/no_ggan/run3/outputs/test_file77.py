from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('task_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows):
    return [dict(row) for row in rows]

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    required = {'task_name', 'description', 'due_date'}
    if not required.issubset(data):
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO tasks (task_name, description, due_date) VALUES (?, ?, ?)',
            (data['task_name'], data['description'], data['due_date'])
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Task added successfully"}), 201

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    conn = get_db_connection()
    try:
        rows = conn.execute(
            'SELECT * FROM tasks WHERE task_name LIKE ? COLLATE NOCASE OR description LIKE ? COLLATE NOCASE',
            (pattern, pattern)
        ).fetchall()
        result = rows_to_dicts(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify(result), 200

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    fields = []
    values = []
    for key in ('task_name', 'description', 'due_date'):
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if not fields:
        return jsonify({"error": "No fields to update provided"}), 400
    values.append(task_id)
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    conn = get_db_connection()
    try:
        conn.execute(sql, values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Task updated successfully"}), 200

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Task deleted successfully"}), 200

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date', '')
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM tasks WHERE due_date = ?', (due_date,)).fetchall()
        result = rows_to_dicts(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)