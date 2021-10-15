import re, importlib, io, zipfile, base64

from threading import Thread
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from tempfile import TemporaryDirectory
from shutil import rmtree
from secrets import token_urlsafe

class CoWrun (Thread) :
    def __init__ (self, source) :
        super().__init__()
        # save files to temp dictectory
        self.tmp = TemporaryDirectory(dir=self.CFG.COW.TMPDIR)
        self.url = self.err = None
        self.source = []
        tmp = Path(self.tmp.name)
        for path, text in source.items() :
            self.add_source(tmp, path, text)
            self.source.append(path)
        self.add_makefile(tmp)
        self.spawn(tmp)
    def add_source (self, tmp, path, text) :
        with (tmp / path).open("w") as out :
            out.write(text)
    def add_makefile (self, tmp) :
        with (tmp / "Makefile").open("w") as make :
            make.write("all:\n"
                       "\t@exit 1\n")
    # match ttyd output
    _ttyd_line = re.compile(r"^\[.*?\]\s*(.*?):\s*(.*)$")
    _ttyd_bind = re.compile("^ERROR on binding fd \d* to port \d* \(.*\)$")
    _ttyd_port = re.compile("^Listening on port: (\d+)$")
    def spawn (self, tmp) :
        # start ttyd
        key = token_urlsafe(10)
        port = None
        while port is None :
            # -p 0 below => ttyd choses a random port
            # if it's already used, we loop to chose another
            self.sub = Popen(["ttyd", "--once", "--base-path", f"/{key}", "-p", "0",
                              "-t", "fontSize=20", "-t", "titleFixed=CoW [run]",
                              "firejail", "--quiet", "--private=.", "--noroot",
                              "bash", "-c",
                              f"make; echo -e '{self.CFG.COW.END_BANNER}'; read"],
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
                        self.url = self.CFG.COW.TTYD_URL.format(port=port, key=key)
                        break
            else :
                # no break => another error
                self.err = "could not start ttyd"
                break
        self.start()
    def run (self) :
        try :
            self.sub.wait(timeout=self.CFG.COW.TTYD_TIMEOUT)
        except TimeoutExpired :
            self.sub.kill()
        finally :
            try :
                self.tmp.cleanup()
            except :
                rmtree(self.tmp.name, ignore_errors=True)

class CoWzip (object) :
    def __init__ (self, source) :
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, mode="w",
                             compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as z :
            for path, data in self.items(source) :
                if getattr(self, "zipname", None) is None :
                    self.zipname = path.with_suffix(".zip").name
                z.writestr(str(path), data)
        self.data = base64.b64encode(stream.getvalue()).decode("utf-8")
    def items (self, project) :
        yield from project.items()

def load (cfg) :
    LANG = cfg.__class__()
    langs = {}
    for name, items in cfg.lang.items() :
        mod = importlib.import_module(f".{name}", "lang")
        mod.CoWrun.CFG = mod.CoWzip.CFG = cfg
        lng = LANG[name] = cfg.__class__({(f"lang_{k}" if k != "lang" else k) : v
                                          for k, v in items.items()})
        ext = lng["lang_ext"] = [e.strip() for e in lng["lang_ext"].split(",")]
        lng.update(run=mod.CoWrun,
                   zip=mod.CoWzip)
    for lng in LANG.values() :
        lng["lang_all"] = {name : LANG[name]["lang_name"] for name in cfg.lang}
    return LANG
