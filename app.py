from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Phishnet Archive</h1><p>This site is a prototype API for the Phishnet GameOfCode project.</p>"