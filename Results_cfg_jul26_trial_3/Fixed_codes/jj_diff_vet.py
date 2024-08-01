import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'recipes.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    conn = create_connection()
    cursor = conn.cursor()

    data = request.get_json()
    title = data.get('title')
    ingredients = data.get('ingredients')

    cursor.execute("INSERT INTO recipes (title, ingredients) VALUES (?, ?)", (title, ingredients))
    recipe_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'recipe_id': recipe_id})

@app.route('/submit_review', methods=['POST'])
def submit_review():
    conn = create_connection()
    cursor = conn.cursor()

    data = request.get_json()
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')

    cursor.execute("INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)", (recipe_id, review, reviewer_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    conn = create_connection()
    cursor = conn.cursor()

    recipe_id = request.args.get('recipe_id')

    cursor.execute("SELECT review, COUNT(*) FROM reviews WHERE recipe_id = ? GROUP BY review", (recipe_id,))
    reviews = cursor.fetchall()

    conn.close()

    return jsonify({'reviews': reviews})

if __name__ == '__main__':
    app.run()