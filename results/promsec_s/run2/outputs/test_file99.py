import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

DATABASE = 'recipe.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                reviewer_id TEXT NOT NULL,
                review TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        conn.commit()
    finally:
        conn.close()


@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    ingredients = data.get('ingredients')
    if not isinstance(title, str) or not isinstance(ingredients, list) or not all(isinstance(i, str) for i in ingredients):
        return jsonify({'error': 'Invalid input'}), 400
    conn = get_db_connection()
    try:
        cur = conn.execute('INSERT INTO recipes (title) VALUES (?)', (title,))
        recipe_id = cur.lastrowid
        for ing in ingredients:
            conn.execute('INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)', (recipe_id, ing))
        conn.commit()
        return jsonify({'message': 'Recipe added', 'recipe_id': recipe_id}), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
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
    if not isinstance(recipe_id, int) or not isinstance(review, str) or not isinstance(reviewer_id, str):
        return jsonify({'error': 'Invalid input'}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO reviews (recipe_id, reviewer_id, review) VALUES (?, ?, ?)',
            (recipe_id, reviewer_id, review)
        )
        conn.commit()
        return jsonify({'message': 'Review submitted'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    recipe_id = request.args.get('recipe_id')
    try:
        recipe_id = int(recipe_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid recipe_id'}), 400
    conn = get_db_connection()
    try:
        rows = conn.execute(
            '''
            SELECT review, COUNT(*) OVER() AS total_count
            FROM reviews
            WHERE recipe_id = ?
            ''',
            (recipe_id,)
        ).fetchall()
        result = [{'review': row['review'], 'total_count': row['total_count']} for row in rows]
        return jsonify(result), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    app.run(debug=False)