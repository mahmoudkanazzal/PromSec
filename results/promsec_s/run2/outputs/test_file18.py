import os
import re
import hmac
import logging
import mimetypes
from flask import Flask, request, jsonify
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPER_SECRET_KEY = os.getenv('SUPER_SECRET_KEY', '')

app = Flask(__name__)

@app.route('/process_order', methods=['POST'])
def process_order():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
        product_id = data['product_id']
        quantity = data['quantity']
        shipping_address = data['shipping_address']
        return jsonify({
            'status': 'processed',
            'product': product_id,
            'quantity': quantity,
            'shipping_to': shipping_address
        })
    except (yaml.YAMLError, ValueError, KeyError):
        return jsonify({'error': 'Invalid request data'}), 400

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('id', '')
    if not re.fullmatch(r'[\w-]*', order_id):
        return jsonify({'error': 'Invalid id parameter'}), 400
    try:
        mime_type = mimetypes.guess_type(order_id)[0]
        logger.info(f'Generated invoice placeholder for order {order_id} with MIME type {mime_type}')
    except Exception as e:
        logger.error(str(e))
    return jsonify({'status': 'Invoice generation initiated'})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key', '')
    if hmac.compare_digest(key, SUPER_SECRET_KEY):
        return jsonify({'status': 'Admin access granted'}), 200
    else:
        return jsonify({'status': 'Access denied'}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        return jsonify({
            'status': 'Inventory updated',
            'new_inventory': data
        })
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400

if __name__ == '__main__':
    app.run(debug=False)