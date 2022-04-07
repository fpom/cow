import re

from . import CoWrun as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    _inbox = re.compile("^--\s*inbox\s*:\s*(.+)$", re.I|re.M)
    _isize = re.compile("^--\s*isize\s*:\s*(.+)$", re.I|re.M)
    _alpha = re.compile("^--\s*alpha\s*:\s*(.+)$", re.I|re.M)
    _tiles = re.compile("^--\s*tiles\s*:\s*(.+)$", re.I|re.M)
    def __init__ (self, source) :
        self.flags = {"-n" : None}
        super().__init__(source)
    def add_source (self, tmp, path, text) :
        super().add_source(tmp, path, text)
        if getattr(self, "main", None) is None :
            self.main = path
        for match in self._inbox.findall(text) :
            self.flags["-i"] = match.group(1).strip()
        for match in self._isize.findall(text) :
            self.flags["-s"] = match.group(1).strip()
        for match in self._alpha.findall(text) :
            if match.group(1).strip().lower() in ("y", "yes", "true", "1") :
                self.flags.pop("-n", None)
            else :
                self.flags["-n"] = None
        for match in self._tiles.findall(text) :
            self.flags["-t"] = match.group(1).strip()
    def add_makefile (self, tmp) :
        flags = " ".join((f"{k} {v}" if v else k) for k, v in self.flags.items())
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make :
            make.write("all:\n"
                       f"\t@echo -e '{self.CFG.COW.RUN_BANNER}'\n"
                       f"\t@echo -ne '{self.CFG.COW.MAKE_PROMPT}'\n"
                       f"\t{self.CFG.LANG.HRM.CMD} {flags} {self.main}\n")

class CoWzip (_CoWzip) :
    pass
