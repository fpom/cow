from flask import Flask, render_template, request, send_file

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index () :
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run () :
    print(request.form)
    return {"link" : "http://www.google.com"}
