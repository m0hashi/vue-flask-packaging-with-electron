from flask import Flask
from flask_restful import Resource, Api
from resources import Pivot
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Awllow CORS
api = Api(app)
api.add_resource(Pivot, '/pivot')
app.run(port=5000, debug=True)



