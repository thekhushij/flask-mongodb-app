# flask-mongodb-app
flask app  with the mongoDB  connection and Kubernetes deployment 
# Flask - MongoDB App

## Run locally
1. start mongodb:
   docker run -d -p 27017:27017 --name mongodb mongo:latest

2. create .env:
   MONGODB_URI=mongodb://localhost:27017/

3. load env and run:
   source venv/bin/activate
   export $(cat .env | xargs)
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=8080

4. Endpoints
   GET  /        -> welcome message
   POST /data    -> insert JSON into Mongo
   GET  /data    -> retrieve all documents
