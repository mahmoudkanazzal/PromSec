from flask import Flask

app = Flask(__name__)

@app.route('/add_user')
def add_user():
    pass

@app.route('/start_task')
def start_task():
    pass

@app.route('/authenticate_admin')
def authenticate_admin():
    pass

@app.route('/update_configuration')
def update_configuration():
    pass

@app.route('/fetch_user_details')
def fetch_user_details():
    pass

@app.route('/delete_user')
def delete_user():
    pass

@app.route('/change_admin_key')
def change_admin_key():
    pass

@app.route('/check_task_status')
def check_task_status():
    pass

@app.route('/set_preferences')
def set_preferences():
    pass

@app.route('/view_logs')
def view_logs():
    pass

@app.route('/export_data')
def export_data():
    pass

@app.route('/view_user_details')
def view_user_details():
    pass

@app.route('/execute_task')
def execute_task():
    pass

@app.route('/view_task_logs')
def view_task_logs():
    pass

if __name__ == '__main__':
    app.run()