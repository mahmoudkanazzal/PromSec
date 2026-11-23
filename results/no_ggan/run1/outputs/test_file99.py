import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('recipe.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    ingredients = data.get('ingredients', [])
    if not isinstance(title, str) or not title.strip():
        return jsonify(error='Title is required and must be a non‑empty string'), 400
    if not isinstance(ingredients, list):
        return jsonify(error='Ingredients must be a list'), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO recipes (title) VALUES (?)', (title.strip(),))
    recipe_id = cur.lastrowid
    for ing in ingredients:
        if isinstance(ing, str):
            cur.execute('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', (recipe_id, ing.strip()))
    conn.commit()
    conn.close()
    return jsonify(message='Recipe added successfully', recipe_id=recipe_id), 201

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json(silent=True) or {}
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    try:
        recipe_id = int(recipe_id)
    except Exception:
        return jsonify(error='recipe_id must be an integer'), 400
    if not isinstance(review, str) or not review.strip():
        return jsonify(error='review is required and must be a non‑empty string'), 400
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        return jsonify(error='reviewer_id is required and must be a non‑empty string'), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (recipe_id, review.strip(), reviewer_id.strip()))
    conn.commit()
    conn.close()
    return jsonify(message='Review submitted successfully'), 200

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    try:
        recipe_id = int(recipe_id)
    except Exception:
        return jsonify(error='recipe_id query parameter must be an integer'), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT review, COUNT(id) AS review_count FROM reviews WHERE recipe_id = ? GROUP BY review', (recipe_id,))
    rows = cur.fetchall()
    conn.close()
    result = [{'review': row['review'], 'review_count': row['review_count']} for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)