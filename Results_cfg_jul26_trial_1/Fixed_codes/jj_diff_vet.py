import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'recipe.db')

def create_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            instructions TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            name TEXT NOT NULL,
            quantity TEXT NOT NULL,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.json
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recipes (name, instructions) VALUES (?, ?)', (data['name'], data['instructions']))
    recipe_id = cursor.lastrowid
    for ingredient in data['ingredients']:
        cursor.execute('INSERT INTO ingredients (recipe_id, name, quantity) VALUES (?, ?, ?)', (recipe_id, ingredient['name'], ingredient['quantity']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Recipe added successfully'})

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.json
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reviews (recipe_id, rating, comment) VALUES (?, ?, ?)', (data['recipe_id'], data['rating'], data['comment']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Review submitted successfully'})

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE recipe_id = ?', (recipe_id,))
    reviews = cursor.fetchall()
    conn.close()
    return jsonify(reviews)

if __name__ == '__main__':
    app.run()