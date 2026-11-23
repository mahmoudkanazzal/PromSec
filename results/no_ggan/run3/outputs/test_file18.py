from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import hmac
import re

app = Flask(__name__)

secret_key = os.getenv('SUPER_SECRET_KEY')
if not secret_key:
    raise RuntimeError("Environment variable SUPER_SECRET_KEY must be set")

@app.route('/process_order', methods=['POST'])
def process_order():
    yaml_order = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(yaml_order)
    except yaml.YAMLError:
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
    if not re.fullmatch(r'\w+', order_id):
        return jsonify({"status": "Invalid order ID"}), 400
    try:
        subprocess.run(['./invoice_generator', order_id], check=True)
    except subprocess.CalledProcessError:
        return jsonify({"status": "Invoice generation failed"}), 500
    except FileNotFoundError:
        return jsonify({"status": "Invoice generator not found"}), 500
    return jsonify({"status": "Invoice generation initiated"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    provided_key = request.form.get('key', '')
    if hmac.compare_digest(provided_key, secret_key):
        return jsonify({"status": "Admin access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    yaml_inventory = request.get_data(as_text=True)
    try:
        inventory_data = yaml.safe_load(yaml_inventory)
    except yaml.YAMLError:
        return jsonify({"status": "Invalid inventory format"}), 400
    return jsonify({
        "status": "Inventory updated",
        "new_inventory": inventory_data
    })

if __name__ == '__main__':
    app.run(debug=False)