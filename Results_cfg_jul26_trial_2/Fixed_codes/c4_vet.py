import os
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

SUPER_SECRET_KEY = os.getenv('SUPER_SECRET_KEY')

@app.route('/process_order', methods=['POST'])
def process_order():
    order_data = yaml.safe_load(request.data)
    # Process order data here
    return jsonify({"message": "Order processed successfully"})

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('id')
    # Generate invoice process
    return jsonify({"message": f"Invoice generated for order ID: {order_id}"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key')
    if key == SUPER_SECRET_KEY:
        return jsonify({"message": "Access granted to admin panel"})
    else:
        return jsonify({"message": "Access denied"})

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    inventory_data = yaml.safe_load(request.data)
    # Update inventory data here
    return jsonify({"message": "Inventory updated successfully"})

if __name__ == '__main__':
    app.run()
