import os
from flask import Flask, request, jsonify, abort
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('recipe.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret')

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    title = data.get('title')
    ingredients = data.get('ingredients')
    if title is None:
        abort(400, description='Missing required field: title')
    if ingredients is None:
        abort(400, description='Missing required field: ingredients')
    if not isinstance(title, str):
        abort(400, description='Field "title" must be a string')
    if not isinstance(ingredients, list):
        abort(400, description='Field "ingredients" must be a list')
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO recipes (title) VALUES (?)', (title,))
        recipe_id = cur.lastrowid
        for ingredient in ingredients:
            if not isinstance(ingredient, str):
                abort(400, description='Each ingredient must be a string')
            cur.execute('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', (recipe_id, ingredient))
        conn.commit()
    return jsonify({'message': 'Recipe added successfully', 'recipe_id': recipe_id}), 201

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    if recipe_id is None:
        abort(400, description='Missing required field: recipe_id')
    if review is None:
        abort(400, description='Missing required field: review')
    if reviewer_id is None:
        abort(400, description='Missing required field: reviewer_id')
    try:
        recipe_id = int(recipe_id)
    except (ValueError, TypeError):
        abort(400, description='Field "recipe_id" must be an integer')
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (recipe_id, review, reviewer_id))
        conn.commit()
    return jsonify({'message': 'Review submitted successfully'}), 200

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    if recipe_id is None:
        abort(400, description='Missing query parameter: recipe_id')
    try:
        recipe_id = int(recipe_id)
    except (ValueError, TypeError):
        abort(400, description='Query parameter "recipe_id" must be an integer')
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT review, COUNT(id) AS review_count FROM reviews WHERE recipe_id = ? GROUP BY review', (recipe_id,))
        rows = cur.fetchall()
    result = [{'review': row['review'], 'review_count': row['review_count']} for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)