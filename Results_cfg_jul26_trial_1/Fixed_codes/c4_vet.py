import os
from flask import Flask, request, jsonify

app = Flask(__name__)

SUPER_SECRET_KEY = os.getenv('SUPER_SECRET_KEY')

@app.route('/process_order', methods=['POST'])
def process_order():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    shipping_address = data.get('shipping_address')
    
    response = {
        'product_id': product_id,
        'quantity': quantity,
        'shipping_address': shipping_address
    }
    
    return jsonify(response)

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('order_id')
    
    # Run external command to generate invoice
    
    response = {
        'order_id': order_id,
        'message': 'Invoice generated successfully'
    }
    
    return jsonify(response)

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    key = request.form.get('key')
    
    if key == SUPER_SECRET_KEY:
        access_status = 'granted'
    else:
        access_status = 'denied'
    
    response = {
        'access_status': access_status
    }
    
    return jsonify(response)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    data = request.get_json()
    
    # Update inventory
    
    response = {
        'message': 'Inventory updated successfully'
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run()