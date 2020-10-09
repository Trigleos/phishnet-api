from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
	with open("content/index.html") as f:
    	return f.read()

@app.route("/network")
def network():
	with open("content/network.html") as f:
    	return f.read()
