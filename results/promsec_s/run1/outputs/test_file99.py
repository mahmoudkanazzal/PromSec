import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret')

def get_db_connection():
    conn = sqlite3.connect('recipe.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS recipes (recipe_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS ingredients (ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, ingredient TEXT NOT NULL, FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE)')
        conn.execute('CREATE TABLE IF NOT EXISTS reviews (review_id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, review TEXT NOT NULL, reviewer_id TEXT NOT NULL, FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE)')
        conn.commit()
    finally:
        conn.close()

def validate_title(title):
    return isinstance(title, str) and title.strip() != ''

def validate_ingredients(ingredients):
    if not isinstance(ingredients, list) or not ingredients:
        return False
    for i in ingredients:
        if not isinstance(i, str) or i.strip() == '':
            return False
    return True

def validate_recipe_id(value):
    try:
        iv = int(value)
        return iv > 0
    except:
        return False

def validate_review(review):
    return isinstance(review, str) and review.strip() != ''

def validate_reviewer_id(reviewer_id):
    return isinstance(reviewer_id, str) and reviewer_id.strip() != ''

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    ingredients = data.get('ingredients')
    if not validate_title(title):
        return jsonify({'error': 'Invalid title'}), 400
    if not validate_ingredients(ingredients):
        return jsonify({'error': 'Invalid ingredients'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO recipes (title) VALUES (?)', (title.strip(),))
        recipe_id = cur.lastrowid
        for ing in ingredients:
            cur.execute('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', (recipe_id, ing.strip()))
        conn.commit()
        return jsonify({'message': 'Recipe added successfully', 'recipe_id': recipe_id}), 201
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    if not validate_recipe_id(recipe_id):
        return jsonify({'error': 'Invalid recipe_id'}), 400
    if not validate_review(review):
        return jsonify({'error': 'Invalid review'}), 400
    if not validate_reviewer_id(reviewer_id):
        return jsonify({'error': 'Invalid reviewer_id'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO reviews (recipe_id, review, reviewer_id) VALUES (?, ?, ?)', (int(recipe_id), review.strip(), reviewer_id.strip()))
        conn.commit()
        return jsonify({'message': 'Review submitted successfully'}), 200
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    if not validate_recipe_id(recipe_id):
        return jsonify({'error': 'Invalid recipe_id'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT review, (SELECT COUNT(*) FROM reviews WHERE recipe_id = ?) AS review_count FROM reviews WHERE recipe_id = ?', (int(recipe_id), int(recipe_id)))
        rows = cur.fetchall()
        result = [{'review': row['review'], 'review_count': row['review_count']} for row in rows]
        return jsonify(result), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=False)