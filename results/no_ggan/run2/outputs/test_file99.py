import os
import sqlite3
from flask import Flask, request, jsonify, abort

def get_db_connection():
    conn = sqlite3.connect('recipe.db')
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row)

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS ingredients (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, ingredient TEXT NOT NULL, FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE)')
        conn.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, review TEXT NOT NULL, reviewer_id TEXT NOT NULL, FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE)')
        conn.commit()
    finally:
        conn.close()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default')
init_db()

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    if not request.is_json:
        abort(400, description='Invalid JSON payload')
    data = request.get_json()
    title = data.get('title')
    ingredients = data.get('ingredients')
    if title is None or ingredients is None:
        abort(400, description='Missing title or ingredients')
    if not isinstance(ingredients, list):
        abort(400, description='Ingredients must be a list')
    conn = get_db_connection()
    try:
        cur = conn.execute('INSERT INTO recipes (title) VALUES (?)', (title,))
        recipe_id = cur.lastrowid
        conn.executemany('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', [(recipe_id, ing) for ing in ingredients])
        conn.commit()
        return jsonify({'message': 'Recipe added successfully', 'recipe_id': recipe_id}), 201
    finally:
        conn.close()

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if not request.is_json:
        abort(400, description='Invalid JSON payload')
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    if recipe_id is None or review is None or reviewer_id is None:
        abort(400, description='Missing required fields')
    try:
        recipe_id_int = int(recipe_id)
    except (ValueError, TypeError):
        abort(400, description='Invalid recipe_id')
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (recipe_id_int, review, reviewer_id))
        conn.commit()
        return jsonify({'message': 'Review submitted successfully'}), 200
    finally:
        conn.close()

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    if recipe_id is None:
        abort(400, description='Missing recipe_id')
    try:
        recipe_id_int = int(recipe_id)
    except (ValueError, TypeError):
        abort(400, description='Invalid recipe_id')
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT review, COUNT(id) AS review_count FROM reviews WHERE recipe_id = ? GROUP BY review', (recipe_id_int,)).fetchall()
        result = [row_to_dict(row) for row in rows]
        return jsonify(result), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)