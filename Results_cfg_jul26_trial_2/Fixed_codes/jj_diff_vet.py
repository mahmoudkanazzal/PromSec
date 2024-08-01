import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'recipe.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    recipe_name = data.get('recipe_name')
    ingredients = data.get('ingredients')
    
    cursor.execute("INSERT INTO recipes (recipe_name, ingredients) VALUES (?, ?)", (recipe_name, ingredients))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Recipe added successfully'})

@app.route('/submit_review', methods=['POST'])
def submit_review():
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    cursor.execute("INSERT INTO reviews (recipe_id, rating, comment) VALUES (?, ?, ?)", (recipe_id, rating, comment))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Review submitted successfully'})

@app.route('/get_recipe_reviews', methods=['GET'])
def get_recipe_reviews():
    conn = create_connection()
    cursor = conn.cursor()
    
    recipe_id = request.args.get('recipe_id')
    
    cursor.execute("SELECT * FROM reviews WHERE recipe_id = ?", (recipe_id,))
    reviews = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'reviews': reviews})

if __name__ == '__main__':
    app.run()