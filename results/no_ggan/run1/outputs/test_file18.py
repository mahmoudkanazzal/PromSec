from flask import Flask, request, jsonify
import os, yaml, subprocess, re

app = Flask(__name__)

secret_key = os.getenv('SUPER_SECRET_KEY')
if not secret_key:
    raise RuntimeError('SUPER_SECRET_KEY environment variable not set')
app.config['SECRET_KEY'] = secret_key

@app.route('/process_order', methods=['POST'])
def process_order():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify(status="Invalid order format"), 400
    if not isinstance(data, dict):
        return jsonify(status="Invalid order format"), 400
    required = ('product_id', 'quantity', 'shipping_address')
    if not all(k in data for k in required):
        return jsonify(status="Missing required order fields"), 400
    return jsonify(status="Order processed", product=data['product_id'], quantity=data['quantity'], shipping_to=data['shipping_address'])

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('id', '')
    if not re.fullmatch(r'\w+', order_id):
        return jsonify(status="Invalid order ID"), 400
    try:
        subprocess.run(['./invoice_generator', order_id], check=True)
    except subprocess.CalledProcessError:
        return jsonify(status="Invoice generation failed"), 500
    except FileNotFoundError:
        return jsonify(status="Invoice generator not found"), 500
    return jsonify(status="Invoice generation initiated")

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key', '')
    if key == secret_key:
        return jsonify(status="Admin access granted")
    return jsonify(status="Access denied"), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify(status="Invalid inventory format"), 400
    return jsonify(status="Inventory updated", new_inventory=data)

if __name__ == '__main__':
    app.run(debug=False)