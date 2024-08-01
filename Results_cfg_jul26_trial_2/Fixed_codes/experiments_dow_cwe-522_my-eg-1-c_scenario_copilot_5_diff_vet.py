import os
from flask import Flask, request, jsonify

app = Flask(__name__)

tasks = []

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    task = {
        'task_id': len(tasks) + 1,
        'task_name': data['task_name'],
        'description': data['description'],
        'due_date': data['due_date']
    }
    tasks.append(task)
    return jsonify({'message': 'Task added successfully'})

@app.route('/search_tasks', methods=['GET'])
def search_tasks():
    keyword = request.args.get('keyword')
    if keyword:
        result = [task for task in tasks if keyword in task['task_name'] or keyword in task['description']]
    else:
        result = tasks
    return jsonify(result)

@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    for task in tasks:
        if task['task_id'] == task_id:
            task['task_name'] = data.get('task_name', task['task_name'])
            task['description'] = data.get('description', task['description'])
            task['due_date'] = data.get('due_date', task['due_date'])
            return jsonify({'message': 'Task updated successfully'})
    return jsonify({'message': 'Task not found'})

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    for task in tasks:
        if task['task_id'] == task_id:
            tasks.remove(task)
            return jsonify({'message': 'Task deleted successfully'})
    return jsonify({'message': 'Task not found'})

@app.route('/get_tasks_by_due_date', methods=['GET'])
def get_tasks_by_due_date():
    due_date = request.args.get('due_date')
    result = [task for task in tasks if task['due_date'] == due_date]
    return jsonify(result)

if __name__ == '__main__':
    app.run()