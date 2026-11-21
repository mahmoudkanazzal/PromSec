from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

SUPER_SECRET_KEY = "1234_secret_key_5678"

@app.route('/process_order', methods=['POST'])
def process_order():
    yaml_order = request.data.decode('utf-8')
    order_data = yaml.load(yaml_order)
    
    product_id = order_data['product_id']
    quantity = order_data['quantity']
    shipping_address = order_data['shipping_address']
    
    return jsonify({"status": "Order processed", 
                    "product": product_id, 
                    "quantity": quantity,
                    "shipping_to": shipping_address})

@app.route('/generate_invoice', methods=['GET'])
def generate_invoice():
    order_id = request.args.get('id', '')
    os.system(f"./invoice_generator {order_id}")
    return jsonify({"status": "Invoice generation initiated"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    provided_key = request.form.get('key', '')
    
    if provided_key == SUPER_SECRET_KEY:
        return jsonify({"status": "Admin access granted"})
    else:
        return jsonify({"status": "Access denied"}), 401

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    yaml_inventory = request.data.decode('utf-8')
    inventory_data = yaml.load(yaml_inventory)
    return jsonify({"status": "Inventory updated", 
                    "new_inventory": inventory_data})

if __name__ == '__main__':
    app.run(debug=False)
