from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# # Use MONGODB_URI environment variable (example: mongodb://user:pass@mongo:27017/)
# MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
# client = MongoClient(MONGODB_URI)
# db = client.flask_db
# collection = db.data

mongo_user = os.environ.get("MONGO_USER")
mongo_pass = os.environ.get("MONGO_PASS")
mongo_host = os.environ.get("MONGO_HOST", "mongo:27017")  # service name in k8s

if mongo_user and mongo_pass:
    MONGODB_URI = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}/?authSource=admin"
else:
    # fallback to .env or local dev
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    
# create mongo client and collection   
client = MongoClient(MONGODB_URI)
db = client.flask_db
collection = db.data

@app.route('/')
def index():
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON supplied"}), 400
        collection.insert_one(json_data)
        return jsonify({"status": "Data inserted"}), 201
    else:
        docs = list(collection.find({}, {"_id": 0}))
        return jsonify(docs), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
