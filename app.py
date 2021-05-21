from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from threading import Thread
from secrets import token_urlsafe
from time import sleep

import re

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from hadlib import getopt

##
##
##

class CoWrun (Thread) :
    _ttyd_line = re.compile(r"^\[.*?\]\s*(.*?):\s*(.*)$")
    _ttyd_bind = re.compile("^ERROR on binding fd \d* to port \d* \(.*\)$")
    _ttyd_port = re.compile("^Listening on port: (\d+)$")
    def __init__ (self, source) :
        super().__init__()
        self.tmp = TemporaryDirectory(dir=".")
        self.url = self.err = None
        tmp = Path(self.tmp.name)
        obj_files = []
        lflags = set()
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
        key = token_urlsafe(10)
        port = None
        finish = "\\n\\n\\033[0;31mtype ENTER to finish\\033[0m"
        while port is None :
            self.sub = Popen(["ttyd", "--once", "--base-path", f"/{key}", "-p", "0",
                              "-t", "fontSize=20",
                              "firejail", "--quiet", "--private=.", "--noroot",
                              "bash", "-c", f"make; echo -e '{finish}'; read"],
                             stdout=PIPE, stderr=STDOUT, cwd=tmp,
                             encoding="utf-8", errors="replace")
            for line in self.sub.stdout :
                if match := self._ttyd_line.match(line.strip()) :
                    flag, message = match.groups()
                    if flag == "E" and self._ttyd_bind.match(message.strip()) :
                        self.sub.kill()
                        break
                    elif flag == "N" and (m := self._ttyd_port.match(message.strip())) :
                        port = m.group(1)
                        self.url = f"http://localhost:{port}/{key}/"
                        break
            else :
                self.err = "could not start ttyd"
                break
        self.start()
    def run (self) :
        try :
            self.sub.wait(timeout=360)
        except TimeoutExpired :
            self.sub.kill()
        finally :
            self.tmp.cleanup()

##
##
##

app = Flask(__name__, template_folder="templates")

if app.config["ENV"] == "development" :
    from colored_traceback import Colorizer

@app.route("/")
def index () :
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run () :
    try :
        handler = CoWrun(dict(request.form))
        if handler.url :
            return {"status" : "OK",
                    "link" : handler.url}
        else :
            return {"status" : handler.err}
    except Exception as err :
        if app.config["ENV"] == "development" :
            coltb = Colorizer(style="default")
            coltb.colorize_traceback(err.__class__, err, err.__traceback__)
            name = err.__class__.__name__
            return {"status" : f"server raised<br/><tt><b>{name}:</b> {err}</tt>"}
        else :
            return {"status" : "internal server error"}

