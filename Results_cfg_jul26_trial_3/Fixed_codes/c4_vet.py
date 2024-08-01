import os
from flask import Flask, request

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

@app.route('/process_order', methods=['POST'])
def process_order():
    # Process order logic here
    return 'Order processed successfully'

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    # Generate invoice logic here
    return 'Invoice generated successfully'

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    # Admin panel logic here
    return 'Admin access granted'

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    # Update inventory logic here
    return 'Inventory updated successfully'

if __name__ == '__main__':
    app.run()