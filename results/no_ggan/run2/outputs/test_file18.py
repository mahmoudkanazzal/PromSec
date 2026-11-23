import os
import re
import yaml
import subprocess
import hmac
from flask import Flask, request, jsonify

app = Flask(__name__)
SUPER_SECRET_KEY = os.getenv('SUPER_SECRET_KEY', 'default_insecure_key')

def is_valid_order_id(order_id):
    return re.fullmatch(r'^[A-Za-z0-9_-]+$', order_id) is not None

@app.route('/process_order', methods=['POST'])
def process_order():
    yaml_order = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(yaml_order)
    except Exception:
        return jsonify({"status": "Invalid order format"}), 400
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    shipping_address = data.get('shipping_address')
    return jsonify({
        "status": "Order processed",
        "product_id": product_id,
        "quantity": quantity,
        "shipping_address": shipping_address
    })

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('id', '')
    if not is_valid_order_id(order_id):
        return jsonify({"status": "Invalid order ID"}), 400
    try:
        result = subprocess.run(['./invoice_generator', order_id], capture_output=True, text=True, check=False)
    except Exception as e:
        return jsonify({"status": "Invoice generation failed", "error": str(e)}), 500
    return jsonify({"status": "Invoice generation initiated", "output": result.stdout})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    provided_key = request.form.get('key', '')
    if hmac.compare_digest(provided_key, SUPER_SECRET_KEY):
        return jsonify({"status": "Admin access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    yaml_inventory = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(yaml_inventory)
    except Exception:
        return jsonify({"status": "Invalid inventory format"}), 400
    return jsonify({"status": "Inventory updated", "new_inventory": data})

if __name__ == '__main__':
    app.run(debug=False)