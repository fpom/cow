from flask import Flask, render_template, request, send_file

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index () :
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run () :
    try :
        source = dict(request.form)
        print(source)
        return {"status" : "OK",
                "link" : "http://www.google.com"}
    except Exception as err :
        if app.config["ENV"] == "development" :
            name = err.__class__.__name__
            return {"status" : f"server raised<br/><tt>{name}: {err}</tt>"}
        else :
            return {"status" : "internal server error"}

