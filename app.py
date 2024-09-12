from flask import Flask, request, jsonify, session, render_template
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from tensorflow.keras.models import load_model
from keras.utils import load_img, img_to_array
import numpy as np
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a secure random key in production

# MongoDB setup
client = MongoClient("mongodb+srv://mahmoud:mahmoud@cluster0.s0qca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Replace with your MongoDB URI
db = client['user_db']
users_collection = db['users']

# Route for signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    existing_user = users_collection.find_one({'username': username})

    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({'username': username, 'password': hashed_password})
    session['username'] = username
    return jsonify({'message': 'Signup successful'}), 201

# Route for login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = users_collection.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Route for logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'You have been logged out'}), 200

# Route for accessing the home page
@app.route('/')
def home():
    if 'username' in session:
        return jsonify({'message': f'Hello, {session["username"]}!'}), 200
    return jsonify({'message': 'Welcome! Please log in or sign up.'}), 200

# Load the model
model_path = os.path.join('model', 'اسم الموديل.h5')
model = None

try:
    model = load_model(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def preprocess_image(img_path):
    img = load_img(img_path, target_size=(128, 128))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array

def predict_image(img_array):
    if model is None:
        return "Model not loaded"
    prediction = model.predict(img_array)
    return 0 if prediction[0][0] > 0.5 else 1

@app.route('/test', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    img_file = request.files['image']
    img_path = os.path.join('uploads', img_file.filename)
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img_file.save(img_path)

    img_array = preprocess_image(img_path)
    prediction = predict_image(img_array)

    return jsonify({"prediction": prediction})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)


    