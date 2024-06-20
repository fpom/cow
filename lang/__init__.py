import re, importlib, io, zipfile, base64, os

from threading import Thread
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from tempfile import TemporaryDirectory
from shutil import rmtree
from secrets import token_urlsafe, randbelow

class CoWrun (Thread) :
    def __init__ (self, source) :
        super().__init__()
        # set language
        lang = self.__class__.__module__
        if lang.startswith("lang.") :
            lang = lang[5:]
        self.CFG["MYLANG"] = lang.upper()
        # save files to temp dictectory
        self.tmp = TemporaryDirectory(dir=self.CFG.COW.TMPDIR)
        self.url = self.err = None
        if getattr(self, "make", None) is None :
            self.make = f"make; echo -e '{self.CFG.COW.END_BANNER}'; read"
        self.env = dict(os.environ)
        self.source = []
        tmp = Path(self.tmp.name)
        for path, text in source.items() :
            self.add_source(tmp, path, text)
            self.source.append(path)
        self.add_makefile(tmp)
        self.timeout = self.CFG.COW.TTYD_TIMEOUT
        self.spawn(tmp)
        self.start()
    def add_source (self, tmp, path, text) :
        with (tmp / path).open("w", encoding="utf-8", errors="replace") as out :
            out.write(text)
        cmt = re.escape(self.CFG.LANG[self.CFG.MYLANG].COMMENT)
        res = re.compile(fr"^{cmt}FILE: (.*)\n{cmt}DATA: data:([^;]+);([^,]+),(.*)$",
                         re.M)
        for match in res.finditer(text) :
            name, mime, base, data = match.group(1, 2, 3, 4)
            tgt = (tmp / path).parent / name
            with tgt.open("wb") as out :
                if base == "base64" :
                    out.write(base64.b64decode(data))
                else :
                    raise ValueError(f"could not handle encoding {base}")
    def add_makefile (self, tmp) :
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make :
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
            # random port withing [49152;65535]
            _port = 49152 + randbelow(16385)
            self.sub = Popen(["ttyd",
                              "--once",
                              "--base-path",
                              f"/{key}",
                              "-p", f"{_port}",
                              "-t", "fontSize=20",
                              "-t", "titleFixed=CoW [run]",
                              "firejail",
                              "--quiet",
                              "--allow-debuggers",
                              "--private=.",
                              "--noroot",
                              "bash", "-c",
                              self.make],
                             stdout=PIPE, stderr=STDOUT, cwd=tmp, env=self.env,
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
    def run (self) :
        try :
            self.sub.wait(timeout=self.timeout)
        except TimeoutExpired :
            self.sub.kill()
        finally :
            try :
                self.tmp.cleanup()
            except :
                rmtree(self.tmp.name, ignore_errors=True)

class CoWrunX (CoWrun) :
    def __init__ (self, source) :
        self.make = "make"
        super().__init__(source)
    # match xpra output
    _xpra_fail = re.compile(r"^failed to setup tcp socket.*Address already in use$")
    _xpra_ready = re.compile(r"^.* xpra is ready\.$")
    def spawn (self, tmp) :
        self.timeout = self.CFG.COW.XPRA_TIMEOUT
        # start xpra
        port = None
        password = token_urlsafe(10)
        env = dict(os.environ, XPRA_PASSWORD=password)
        html5 = Path("xpra-html5").resolve()
        child = (f"firejail --quiet --private=. --noroot"
                 f" xterm -fa Monospace -fs 16 -e {self.make}")
        while port is None :
            # random port withing [49152;65535]
            _port = 49152 + randbelow(16385)
            self.sub = Popen(["xpra", "start",
                              "--daemon=no",
                              "--mdns=no",
                              "--exit-with-children=yes",
                              "--exit-with-client=yes",
                              "--dpi=96",
                              "--file-transfer=off",
                              "--open-files=off",
                              "--forward-xdg-open=off",
                              "--idle-timeout=600",
                              "--system-tray=no",
                              "--bell=no",
                              "--webcam=no",
                              "--tcp-auth=env",
                              f"--html={html5}",
                              f"--bind-tcp=0.0.0.0:{_port}",
                              f"--start-child={child}"],
                             stdout=PIPE, stderr=STDOUT, cwd=tmp, env=env,
                             encoding="utf-8", errors="replace")
            for line in self.sub.stdout :
                _line = line.strip()
                if self._xpra_fail.match(_line) :
                    # failed to bind port
                    self.sub.kill()
                    break
                elif self._xpra_ready.match(_line) :
                    port = _port
                    self.url = self.CFG.COW.XPRA_URL.format(port=port, password=password)
                    break
            else :
                # no break => another error
                self.err = "could not start xpra"
                break

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
    for name, items in cfg.LANG.items() :
        if not items["ENABLED"] :
            continue
        mod = importlib.import_module(f".{name.lower()}", "lang")
        mod.CoWrun.CFG = mod.CoWzip.CFG = cfg
        lng = LANG[name] = cfg.__class__({(f"LANG_{k}" if k != "LANG" else k) : v
                                          for k, v in items.items()})
        lng["LANG_EXT"] = [e.strip() for e in lng["LANG_EXT"].split(",")]
        if "LANG_MODENAME" not in lng :
            lng["LANG_MODENAME"] = Path(lng["LANG_MODE"]).stem
        lng.update(run=mod.CoWrun,
                   zip=mod.CoWzip)
    lang_all = {name : conf["LANG_NAME"] for name, conf in LANG.items()}
    for lng in LANG.values() :
        lng["LANG_ALL"] = lang_all
    return LANG
