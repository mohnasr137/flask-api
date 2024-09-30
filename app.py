import os
import random
import datetime
from flask import Flask, request, render_template, send_from_directory, jsonify, session  # type: ignore
from pymongo import MongoClient # type: ignore
from diffusers import StableDiffusionPipeline  # type: ignore
from PIL import Image  # type: ignore
import torch  # type: ignore
import torch.nn as nn  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a secure random key in production

# MongoDB setup
client = MongoClient("mongodb+srv://mahmoud:mahmoud@cluster0.s0qca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Replace with your MongoDB URI
db = client['user_db']
users_collection = db['users']
paths_collection = db['paths']

# Path to the locally stored pretrained model (just the .pth file)
model_path = os.path.join(os.path.dirname(__file__), 'full_model.pth')
model = torch.load(model_path)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Folder to save generated images
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'out_put')
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Route for home
@app.route("/home", methods=["GET"])
def index():
    return render_template("index.html", image_path=None)

# Route for logo
@app.route('/logo', methods=["GET"])
def logo():
    return send_from_directory('static', 'logo.png')

# Route for favicon
@app.route('/favicon', methods=["GET"])
def favicon():
    return send_from_directory('static', 'favicon.ico')

# Route for image
@app.route("/image", methods=["POST"])
def index():
        data = request.get_json()
        username = data.get('username')
        prompt = request.form.get("prompt")
        image = model(prompt).images[0]
        random_number = random.randint(1000, 9999)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_image_{timestamp}_{random_number}.png"
        image_path = os.path.join(OUTPUT_FOLDER, filename)
        image.save(image_path)
        paths_collection.insert_one({'username': username, 'path': image_path})
        return render_template("index.html", image_path=image_path)

# Route for output
@app.route('/output/<filename>', methods=["GET"])
def output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# Route for signup
@app.route('/signup', methods=['Post'])
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

# Route for signupPage
@app.route('/signupPage', methods=['GET'])
def signup():
    return render_template("signup.html", image_path=None)

# Route for login
@app.route('/login', methods=['Post'])
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

# Route for loginPage
@app.route('/loginPage', methods=['GET'])
def login():
    return render_template("login.html", image_path=None)

# Route for logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'You have been logged out'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
