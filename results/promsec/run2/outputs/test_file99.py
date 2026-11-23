import os
import _sqlite3
from sqlite3 import connect
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    return connect('recipe.db', detect_types=_sqlite3.PARSE_DECLTYPES)

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    data = request.get_json()
    title = data.get('title')
    ingredients = data.get('ingredients')
    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'Title must be a non-empty string'}), 400
    if not isinstance(ingredients, list) or not ingredients:
        return jsonify({'error': 'Ingredients must be a non-empty list'}), 400
    for ing in ingredients:
        if not isinstance(ing, str) or not ing.strip():
            return jsonify({'error': 'Each ingredient must be a non-empty string'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO recipes (title) VALUES (?)', (title.strip(),))
        recipe_id = cur.lastrowid
        for ing in ingredients:
            cur.execute('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', (recipe_id, ing.strip()))
        conn.commit()
        return jsonify({'message': 'Recipe added successfully', 'recipe_id': recipe_id}), 201
    except _sqlite3.Error:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    if not isinstance(recipe_id, int):
        return jsonify({'error': 'recipe_id must be an integer'}), 400
    if not isinstance(reviewer_id, int):
        return jsonify({'error': 'reviewer_id must be an integer'}), 400
    if not isinstance(review, str) or not review.strip():
        return jsonify({'error': 'review must be a non-empty string'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (recipe_id, review.strip(), reviewer_id))
        conn.commit()
        return jsonify({'message': 'Review submitted successfully'}), 200
    except _sqlite3.Error:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    try:
        recipe_id_int = int(recipe_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'recipe_id query parameter must be an integer'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT r.review, COUNT(r.id) AS review_count FROM reviews r WHERE r.recipe_id = ? GROUP BY r.id', (recipe_id_int,))
        rows = cur.fetchall()
        result = [{'review': row[0], 'review_count': row[1]} for row in rows]
        return jsonify(result), 200
    except _sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)