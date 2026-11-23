from flask import Flask, request, jsonify
import yaml
import re
from os import getenv

app = Flask(__name__)

SUPER_SECRET_KEY = getenv('SUPER_SECRET_KEY', 'default_fallback_key')

def _is_valid_invoice_id(invoice_id: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_-]+", invoice_id) is not None

def _generate_invoice(invoice_id: str) -> None:
    # Placeholder for real invoice generation logic
    pass

@app.route('/process_order', methods=['POST'])
def process_order():
    raw = request.get_data()
    data = yaml.safe_load(raw.decode('utf-8'))
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    shipping_address = data.get('shipping_address')
    return jsonify({
        'status': 'Order processed',
        'product_id': product_id,
        'quantity': quantity,
        'shipping_address': shipping_address
    })

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    invoice_id = request.args.get('id', '')
    if not _is_valid_invoice_id(invoice_id):
        return jsonify({'status': 'Invalid invoice ID'}), 400
    _generate_invoice(invoice_id)
    return jsonify({'status': 'Invoice generation initiated'})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key', '')
    if key == SUPER_SECRET_KEY:
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    raw = request.get_data()
    inventory = yaml.safe_load(raw.decode('utf-8'))
    return jsonify({
        'status': 'Inventory updated',
        'new_inventory': inventory
    })

if __name__ == '__main__':
    app.run(debug=False)