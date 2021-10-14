from pathlib import Path

from flask import Flask, render_template, request, session, redirect, url_for, \
    jsonify, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

##
## configuration
##

DEFAULT_CFG = """
[COW]
# URL on which ttyd will be reachable, parametrized with {port} and {key}
#
# For example, a reverse proxy may redirect
# "hostname/ttyd/{port}/{key}/" to "localhost:{port}/{key}/"
# in which case you may use "https://hostname/ttyd/{port}/{key}/"
#
# Default value "http://localhost:{port}/{key}/" is for direct connection
# when the server is run locally
TTYD_URL = "http://localhost:{port}/{key}/"

# timeout before to kill ttyd, default to 6 minutes (360 seconds)
TTYD_TIMEOUT = 360

# where to store user's files
TMPDIR = "/tmp"

# secret key to secure cookies
# put whatever you want, keep it secret
SECRET_KEY = "secret random stuff"

# what to print on term before compilation
# may contain ANSI escape codes for colors
GCC_BANNER = "\\033[1;31mCOMPILING\\033[0m"

# what to print on term between compilation and execution
# may contain ANSI escape codes for colors
RUN_BANNER = "\\n\\n\\033[1;31mRUNNING\\033[0m"

# what to print on term when compilation/execution is finished
# may contain ANSI escape codes for colors
END_BANNER = "\\n\\n\\033[1;31mALL DONE, type ENTER to finish\\033[0m"

# what to print as a fake prompt for Makefile commands
# may contain ANSI escape codes for colors
MAKE_PROMPT = "\\033[1;32m#\\033[0m "

# authentication:
#  - None  => no authentication
#  - "CAS" => CAS authentication
AUTH = None

# when AUTH = "CAS", server URL
CAS_SERVER = "https://sso.pdx.edu"

[LANG:C]
NAME = C11
EXT = .c, .h
MODE = clike/clike.js

[LANG:PROCESSING]
NAME = Processing 3
EXT = .pde
MODE = clike/clike.js
"""

import configparser, ast, os
import lang

class Config (dict) :
    @classmethod
    def load (cls) :
        self = cls()
        cfg = configparser.ConfigParser()
        cfg.read_string(DEFAULT_CFG)
        cfg.read([Path(__file__).parent / "cow.ini",
                  Path(os.environ.get("COW_CONFIG", ""))])
        for sec, items in cfg.items() :
            top = self
            lang = None
            for part in sec.lower().split(":") :
                if part not in top :
                    top[part] = cls()
                top = top[part]
                if lang is None and part == "lang" :
                    lang = True
                elif lang :
                    top["lang"] = part
                    lang = False
            for key, val in items.items() :
                try :
                    top[key.lower()] = ast.literal_eval(val)
                except :
                    top[key.lower()] = val
        return self
    def __getattr__ (self, name) :
        return self[name.lower()]
    def __matmul__ (self, name) :
        return {k : v for k, v in self.items() if k.startswith(name)}

CFG = Config.load()
LANG = lang.load(CFG)

##
## Flask part
##

app = Flask(__name__, template_folder="templates")
app.secret_key = CFG.COW.SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

if CFG.COW.AUTH == "CAS" :
    from flask_cas import CAS
    CAS(app)
    app.config["CAS_SERVER"] = CFG.COW.CAS_SERVER
    app.config["CAS_AFTER_LOGIN"] = "index"

if app.config["ENV"] == "development" :
    # print exceptions on stdout
    try :
        # try to colorize them
        from colored_traceback import Colorizer
        coltb = Colorizer(style="default")
        print_exception = coltb.colorize_traceback
    except ImportError :
        from traceback import print_exception

@app.route("/", defaults={"lang" : "c"})
@app.route("/<lang>")
def index (lang) :
    if CFG.COW.AUTH == "CAS" :
        user = session.get(app.config["CAS_USERNAME_SESSION_KEY"], None)
        if user is None :
            return redirect(url_for("cas.login"))
        session["username"] = user
    try :
        print(LANG[lang] @ "lang")
        return render_template("index.html", **(LANG[lang] @ "lang"))
    except KeyError :
        abort(404)

@app.route("/<lang>.js")
def cow_js (lang) :
    if CFG.COW.AUTH and session.get("username", None) is None :
        abort(401)
    try :
        return render_template("cow.js", **(LANG[lang] @ "lang"))
    except KeyError :
        abort(404)

@app.route("/run/<lang>", methods=["POST"])
def run (lang) :
    if CFG.COW.AUTH and session.get("username", None) is None :
        return jsonify({"status" : "not authenticated"})
    try :
        runner = LANG[lang].run({Path(p) : d for p, d in request.form.items()})
    except KeyError :
        abort(404)
    try :
        if runner.url :
            return jsonify({"status" : "OK",
                            "link" : runner.url})
        else :
            return jsonify({"status" : runner.err})
    except Exception as err :
        if app.config["ENV"] == "development" :
            print_exception(err.__class__, err, err.__traceback__)
        return jsonify({"status" : "internal server error"})

@app.route("/dl/<lang>", methods=["POST"])
def dl (lang) :
    if CFG.COW.AUTH and session.get("username", None) is None :
        return jsonify({"status" : "not authenticated"})
    try :
        zipper = LANG[lang].zip({Path(secure_filename(n)) : d
                                 for n, d in request.form.items()})
    except KeyError :
        abort(404)
    return jsonify({"status" : "OK",
                    "filename" : str(zipper.zipname),
                    "data" : zipper.data})
