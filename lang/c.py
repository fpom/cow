import re, shlex

from hadlib import getopt

from . import CoWrun as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    _gcc_opt = re.compile("^//\s*gcc\s*:\s*(.+)$", re.I|re.M)
    _ldd_opt = re.compile("^//\s*ldd\s*:\s*(.+)$", re.I|re.M)
    _arg_opt = re.compile("^//\s*arg\s*:\s*(.+)$", re.I|re.M)
    _env_opt = re.compile("^//\s*env\s*:\s*(.+)$", re.I|re.M)
    _run_opt = re.compile("^//\s*run\s*:\s*(.+)$", re.I|re.M)
    def __init__ (self, source) :
        self._cf = {}
        self._lf = set()
        self.argv = ""
        self.envt = {}
        super().__init__(source)
    def add_source (self, tmp, path, text) :
        super().add_source(tmp, path, text)
        cf, lf = getopt([tmp / path], "linux", "gcc")
        for match in self._gcc_opt.findall(text) :
            cf.update(shlex.split(match))
        for match in self._ldd_opt.findall(text) :
            lf.update(shlex.split(match))
        self._lf.update(lf)
        self._cf[path] = cf
        for match in self._arg_opt.findall(text) :
            self.argv = match.strip()
        for match in self._run_opt.findall(text) :
            self.make = match.strip()
        for match in self._env_opt.findall(text) :
            try :
                key, val = match.split("=", 1)
            except :
                continue
            self.envt[key.strip()] = val.strip()
    def add_makefile (self, tmp) :
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make :
            make.write("all:"
                       "\n\t"
                       f"@echo -e '{self.CFG.COW.GCC_BANNER}'"
                       "\n")
            obj_files = []
            for path in self.source :
                if not path.suffix.lower() == ".c" :
                    continue
                cf = self._cf[path]
                objpath = path.with_suffix(".o")
                obj_files.append(str(objpath))
                make.write("\t"
                           f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                           "\n\t"
                           f"{self.CFG.LANG.C.CMD} {path} -o {objpath}"
                           "\n")
            env = "  ".join(f"{key}={shlex.join([val])}"
                            for key, val in self.envt.items())
            if env :
                env += " "
            make.write("\t"
                       f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                       "\n\t"
                       f"gcc {' '.join(obj_files)} {' '.join(self._lf)} -o a.out"
                       "\n\t"
                       f"@echo -e '{self.CFG.COW.RUN_BANNER}'"
                       "\n\t"
                       f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                       "\n\t"
                       f"{env}./a.out {self.argv}"
                       "\n")

class CoWzip (_CoWzip) :
    pass
