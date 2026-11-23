import os, hmac, mimetypes
from flask import Flask, request, jsonify
from yaml import safe_load as yaml_load
app = Flask(__name__)
app.secret_key = os.getenv('SUPER_SECRET_KEY', '')
@app.route('/process_order', methods=['POST'])
def process_order():
    try:
        data = yaml_load(request.get_data(as_text=True))
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid input'}), 400
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    shipping_address = data.get('shipping_address')
    if not isinstance(product_id, str) or not isinstance(shipping_address, str) or not isinstance(quantity, int):
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'processed', 'product': product_id, 'quantity': quantity, 'shipping_to': shipping_address}), 200
@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    invoice_id = request.args.get('id', '')
    try:
        mimetypes.guess_type(invoice_id)
    except Exception:
        return jsonify({'error': 'Invoice generation failed'}), 500
    return jsonify({'status': 'Invoice generation initiated'}), 200
@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key', '')
    if hmac.compare_digest(key, app.secret_key):
        return jsonify({'status': 'Admin access granted'}), 200
    return jsonify({'status': 'Access denied'}), 401
@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    try:
        data = yaml_load(request.get_data(as_text=True))
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Inventory updated', 'new_inventory': data}), 200
if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False)