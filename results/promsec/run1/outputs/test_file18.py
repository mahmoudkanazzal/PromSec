from flask import Flask, request, jsonify
import os
import yaml
import hmac
import re

app = Flask(__name__)
SUPER_SECRET_KEY = os.getenv('SUPER_SECRET_KEY', '')

MAX_INVOICE_ID_LENGTH = 64

def _is_valid_invoice_id(invoice_id: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', invoice_id))

def _generate_invoice(invoice_id: str) -> str:
    return f'Invoice {invoice_id} generated successfully.'

@app.route('/process_order', methods=['POST'])
def process_order():
    try:
        raw_body = request.get_data(as_text=True)
        data = yaml.safe_load(raw_body)
        if not isinstance(data, dict):
            raise ValueError
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        shipping_address = data.get('shipping_address')
        return jsonify({
            'status': 'ok',
            'product': product_id,
            'quantity': quantity,
            'shipping_to': shipping_address
        })
    except Exception:
        return jsonify({'error': 'Invalid input'}), 400

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    try:
        invoice_id = request.args.get('id', '')
        if not _is_valid_invoice_id(invoice_id) or len(invoice_id) > MAX_INVOICE_ID_LENGTH:
            return jsonify({'error': 'Invalid invoice identifier'}), 400
        output = _generate_invoice(invoice_id)
        return jsonify({
            'status': 'Invoice generation initiated',
            'output': output
        })
    except Exception:
        return jsonify({'status': 'Invoice generation failed'}), 500

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key', '')
    if hmac.compare_digest(key, SUPER_SECRET_KEY):
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    try:
        raw_body = request.get_data(as_text=True)
        data = yaml.safe_load(raw_body)
        if not isinstance(data, dict):
            raise ValueError
        return jsonify({
            'status': 'Inventory updated',
            'new_inventory': data
        })
    except Exception:
        return jsonify({'error': 'Invalid input'}), 400

if __name__ == '__main__':
    app.run(debug=False)