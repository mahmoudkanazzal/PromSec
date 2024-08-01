import os
from flask import Flask, request, jsonify

app = Flask(__name__)

super_secret_key = os.environ.get('SUPER_SECRET_KEY')

inventory = {
    'apple': 10,
    'banana': 15,
    'orange': 20
}

@app.route('/process_order', methods=['POST'])
def process_order():
    data = request.get_json()
    item = data.get('item')
    quantity = data.get('quantity')

    if item in inventory and inventory[item] >= quantity:
        inventory[item] -= quantity
        return jsonify({'message': 'Order processed successfully'})
    else:
        return jsonify({'message': 'Not enough stock'})

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    data = request.get_json()
    item = data.get('item')
    quantity = data.get('quantity')
    total_price = 0

    if item in inventory:
        total_price = quantity * inventory[item]
        return jsonify({'total_price': total_price})
    else:
        return jsonify({'message': 'Item not found'})

@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    if request.headers.get('super_secret_key') == super_secret_key:
        return jsonify({'inventory': inventory})
    else:
        return jsonify({'message': 'Unauthorized'})

@app.route('/update_inventory', methods=['PUT'])
def update_inventory():
    if request.headers.get('super_secret_key') == super_secret_key:
        data = request.get_json()
        item = data.get('item')
        quantity = data.get('quantity')

        if item in inventory:
            inventory[item] = quantity
            return jsonify({'message': 'Inventory updated successfully'})
        else:
            return jsonify({'message': 'Item not found'})
    else:
        return jsonify({'message': 'Unauthorized'})

if __name__ == '__main__':
    app.run()