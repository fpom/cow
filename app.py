from flask import Flask, render_template, request, send_file

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index () :
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run () :
    source = request.form["source"]
    return {"link" : "http://www.google.com"}
