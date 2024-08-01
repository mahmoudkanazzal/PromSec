import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'recipe.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json()
    recipe_title = data.get('recipe_title')
    ingredients = data.get('ingredients')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO recipes (title) VALUES (?)', (recipe_title,))
    recipe_id = cursor.lastrowid

    for ingredient in ingredients:
        cursor.execute('INSERT INTO ingredients (recipe_id, name) VALUES (?, ?)', (recipe_id, ingredient))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Recipe added successfully', 'recipe_id': recipe_id})

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (recipe_id, review, reviewer_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Review submitted successfully'})

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT review, COUNT(*) as count FROM reviews WHERE recipe_id = ? GROUP BY review', (recipe_id,))
    reviews = cursor.fetchall()

    conn.close()

    return jsonify({'reviews': [dict(review) for review in reviews]})

if __name__ == '__main__':
    app.run()