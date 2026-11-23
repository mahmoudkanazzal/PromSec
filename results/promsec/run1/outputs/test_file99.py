from flask import Flask, request, jsonify
import sqlite3 as db
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = db.connect('recipe.db')
    conn.row_factory = db.Row
    return conn

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    ingredients = data.get('ingredients')
    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'Invalid title'}), 400
    if not isinstance(ingredients, list) or not all(isinstance(i, str) and i.strip() for i in ingredients):
        return jsonify({'error': 'Invalid ingredients'}), 400
    try:
        conn = get_db_connection()
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
    data = request.get_json(silent=True) or {}
    recipe_id = data.get('recipe_id')
    review = data.get('review')
    reviewer_id = data.get('reviewer_id')
    if not isinstance(recipe_id, int):
        return jsonify({'error': 'Invalid recipe_id'}), 400
    if not isinstance(reviewer_id, int):
        return jsonify({'error': 'Invalid reviewer_id'}), 400
    if not isinstance(review, str) or not review.strip():
        return jsonify({'error': 'Invalid review'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO reviews (recipe_id, reviewer_id, review) VALUES (?, ?, ?)', (recipe_id, reviewer_id, review.strip()))
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
    try:
        recipe_id_int = int(recipe_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid or missing recipe_id'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT r.review, COUNT(r.id) AS review_count FROM reviews r WHERE r.recipe_id = ? GROUP BY r.id', (recipe_id_int,))
        rows = cur.fetchall()
        result = [{'review': row['review'], 'review_count': row['review_count']} for row in rows]
        return jsonify(result), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)