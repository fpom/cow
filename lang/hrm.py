import re

from . import CoWrun as _CoWrun, CoWzip as _CoWzip


class CoWrun(_CoWrun):
    _inbox = re.compile(r"^--\s*inbox\s*:\s*(.+)$", re.I | re.M)
    _isize = re.compile(r"^--\s*isize\s*:\s*(.+)$", re.I | re.M)
    _alpha = re.compile(r"^--\s*alpha\s*:\s*(.+)$", re.I | re.M)
    _neg = re.compile(r"^--\s*neg\s*:\s*(.+)$", re.I | re.M)
    _max = re.compile(r"^--\s*max\s*:\s*(.+)$", re.I | re.M)
    _tiles = re.compile(r"^--\s*tiles\s*:\s*(.+)$", re.I | re.M)
    _gui = re.compile(r"^--\s*gui\s*:\s*(.+)$", re.I | re.M)

    def __init__(self, source):
        self.flags = {}
        super().__init__(source)

    def add_source(self, tmp, path, text):
        super().add_source(tmp, path, text)
        if getattr(self, "main", None) is None:
            self.main = path
        self.flags["cmd"] = "play"
        for match in self._inbox.findall(text):
            self.flags["-i"] = match.strip()
        for match in self._isize.findall(text):
            self.flags["-l"] = match.strip()
        for match in self._alpha.findall(text):
            if match.strip().lower() in ("y", "yes", "true", "1"):
                self.flags["-c"] = None
            else:
                self.flags.pop("-c", None)
        for match in self._neg.findall(text):
            if match.strip().lower() in ("y", "yes", "true", "1"):
                self.flags["-n"] = None
            else:
                self.flags.pop("-n", None)
        for match in self._tiles.findall(text):
            self.flags["-t"] = match.strip()
        for match in self._max.findall(text):
            try:
                self.flags["-m"] = int(match.strip())
            except ValueError:
                pass
        for match in self._gui.findall(text):
            if match.strip().lower() in ("n", "no", "false", "0"):
                self.flags["cmd"] = "run"
                self.flags["-v"] = None
            else:
                self.flags["cmd"] = "play"
                self.flags.pop("-v", None)

    def add_makefile(self, tmp):
        cmd = self.flags["cmd"]
        flags = " ".join((f"{k} {v}" if v is not None else k)
                         for k, v in self.flags.items()
                         if k.startswith("-"))
        with (tmp / "Makefile").open("w",
                                     encoding="utf-8",
                                     errors="replace") as make:
            make.write(
                "all:\n"
                 f"\t@echo -e '{self.CFG.COW.RUN_BANNER}'\n"
                 f"\t@echo -ne '{self.CFG.COW.MAKE_PROMPT}'\n"
                 f"\t{self.CFG.LANG.HRM.CMD} {cmd} {flags} {self.main}\n")


class CoWzip(_CoWzip):
    pass
