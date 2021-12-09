from . import CoWrun as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    def add_source (self, tmp, path, text) :
        super().add_source(tmp, path, text)
        if getattr(self, "main", None) is None :
            self.main = path
    def add_makefile (self, tmp) :
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make :
            make.write("all:\n"
                       f"\t@echo -e '{self.CFG.COW.RUN_BANNER}'\n"
                       f"\t@echo -ne '{self.CFG.COW.MAKE_PROMPT}'\n"
                       f"\t{self.CFG.LANG.PYTHON.CMD} {self.main}\n")

class CoWzip (_CoWzip) :
    pass
