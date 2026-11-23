import sqlite3
import sys

DB_FILE = 'inventory.db'
PASSWORD = 'shop123'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 quantity INTEGER NOT NULL,
                 price REAL NOT NULL)''')
    conn.commit()
    conn.close()

def verify_password():
    pwd = input('Enter password: ')
    return pwd == PASSWORD

def add_item(name, quantity, price):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO items (name, quantity, price) VALUES (?,?,?)',
              (name, quantity, price))
    conn.commit()
    conn.close()
    print('Item added.')

def remove_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    print('Item removed.')

def update_quantity(item_id, quantity):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE items SET quantity=? WHERE id=?',
              (quantity, item_id))
    conn.commit()
    conn.close()
    print('Quantity updated.')

def list_items():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name, quantity, price FROM items')
    rows = c.fetchall()
    conn.close()
    if not rows:
        print('No items in inventory.')
        return
    print('{:<4} {:<20} {:<8} {:<8}'.format('ID','Name','Qty','Price'))
    for r in rows:
        print('{:<4} {:<20} {:<8} ${:<7.2f}'.format(r[0], r[1], r[2], r[3]))

def main_menu():
    print('\nInventory Management')
    print('1. List items')
    print('2. Add item')
    print('3. Remove item')
    print('4. Update quantity')
    print('5. Exit')
    choice = input('Select option: ')
    return choice.strip()

def main():
    init_db()
    if not verify_password():
        print('Access denied.')
        sys.exit(1)
    while True:
        choice = main_menu()
        if choice == '1':
            list_items()
        elif choice == '2':
            name = input('Item name: ')
            qty = int(input('Quantity: '))
            price = float(input('Price: '))
            add_item(name, qty, price)
        elif choice == '3':
            item_id = int(input('Item ID to remove: '))
            remove_item(item_id)
        elif choice == '4':
            item_id = int(input('Item ID to update: '))
            qty = int(input('New quantity: '))
            update_quantity(item_id, qty)
        elif choice == '5':
            print('Goodbye.')
            break
        else:
            print('Invalid choice.')

if __name__ == '__main__':
    main()