##
## CONFIGURATION
##

# The configuration options below may be duplicated in an external
# file to avoid overwritting them on update. In such a case, set
# environment variable COW_CONFIG to the path of this file, it will be
# loaded at startup and will override the values below.

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

# secret key to secure cookies
# put whatever you want, keep it secret
SECRET_KEY = "secret random stuff"

# what to print on term when compilation/execution is finished
# may contain ANSI escape codes for colors
END_BANNER = "\\n\\n\\033[0;31mtype ENTER to finish\\033[0m"

# authentication:
#  - None => no authentication
#  - CAS => CAS authentication
AUTH = None

# when AUTH = "CAS", server URL
CAS_SERVER = "https://sso.pdx.edu"

##
## END OF CONFIGURATION
##

from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from threading import Thread
from secrets import token_urlsafe
from time import sleep

import re, os

from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename

exec(Path(os.environ.get("COW_CONFIG", "/dev/null")).read_text())

if AUTH == "CAS" :
    from flask_cas import CAS

from hadlib import getopt

##
## C stuff
##

class CoWrun (Thread) :
    # match ttyd output
    _ttyd_line = re.compile(r"^\[.*?\]\s*(.*?):\s*(.*)$")
    _ttyd_bind = re.compile("^ERROR on binding fd \d* to port \d* \(.*\)$")
    _ttyd_port = re.compile("^Listening on port: (\d+)$")
    def __init__ (self, source) :
        super().__init__()
        # save files to temp dictectory
        self.tmp = TemporaryDirectory(dir=".")
        self.url = self.err = None
        tmp = Path(self.tmp.name)
        obj_files = []
        lflags = set()
        # add Makefile also
        with (tmp / "Makefile").open("w") as make :
            make.write("all:" "\n")
            for path, text in source.items() :
                path = tmp / secure_filename(path)
                with path.open("w") as out :
                    out.write(text)
                cf, lf = getopt([path], "linux", "gcc")
                lflags.update(lf)
                srcpath = path.relative_to(tmp)
                objpath = srcpath.with_suffix(".o")
                obj_files.append(str(objpath))
                make.write("\t"
                           f"gcc -c -g -fno-inline -fno-omit-frame-pointer -std=c11"
                           f" -Wall -Wpedantic {' '.join(cf)}"
                           f" {srcpath} -o {objpath}"
                           "\n")
            make.write("\t"
                       f"gcc {' '.join(obj_files)} {' '.join(lflags)} -o a.out"
                       "\n\t"
                       f"./a.out"
                       "\n")
        # start ttyd
        key = token_urlsafe(10)
        port = None
        while port is None :
            # -p 0 below => ttyd choses a random port
            # if it's already used, we loop to chose another
            self.sub = Popen(["ttyd", "--once", "--base-path", f"/{key}", "-p", "0",
                              "-t", "fontSize=20",
                              "firejail", "--quiet", "--private=.", "--noroot",
                              "bash", "-c", f"make; echo -e '{END_BANNER}'; read"],
                             stdout=PIPE, stderr=STDOUT, cwd=tmp,
                             encoding="utf-8", errors="replace")
            for line in self.sub.stdout :
                match = self._ttyd_line.match(line.strip())
                if match :
                    flag, message = match.groups()
                    if flag == "E" and self._ttyd_bind.match(message.strip()) :
                        # ttyd failed to bind port
                        self.sub.kill()
                        break
                    m = self._ttyd_port.match(message.strip())
                    if flag == "N" and m :
                        # ttyd succeeded to bind port
                        port = m.group(1)
                        self.url = TTYD_URL.format(port=port, key=key)
                        break
            else :
                # no break => another error
                self.err = "could not start ttyd"
                break
        self.start()
    def run (self) :
        try :
            self.sub.wait(timeout=TTYD_TIMEOUT)
        except TimeoutExpired :
            self.sub.kill()
        finally :
            self.tmp.cleanup()

##
## W stuff
##

app = Flask(__name__, template_folder="templates")
app.secret_key = SECRET_KEY

if AUTH == "CAS" :
    CAS(app)
    app.config["CAS_SERVER"] = CAS_SERVER
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

@app.route("/")
def index () :
    if AUTH == "CAS" :
        user = session.get(app.config["CAS_USERNAME_SESSION_KEY"], None)
        if user is None :
            return redirect(url_for("cas.login"))
        session["username"] = user
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run () :
    if AUTH :
        if session.get("username", None) is None :
            return {"status" : "not authenticated"}
    try :
        handler = CoWrun(dict(request.form))
        if handler.url :
            return {"status" : "OK",
                    "link" : handler.url}
        else :
            return {"status" : handler.err}
    except Exception as err :
        if app.config["ENV"] == "development" :
            print_exception(err.__class__, err, err.__traceback__)
        return {"status" : "internal server error"}

