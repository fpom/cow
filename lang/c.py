import re, shlex

from hadlib import getopt

from . import CoWrun as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    _gcc_opt = re.compile("^//\s*gcc\s*:\s*(.+)$", re.I|re.M)
    _ldd_opt = re.compile("^//\s*ldd\s*:\s*(.+)$", re.I|re.M)
    def __init__ (self, source) :
        self._cf = {}
        self._lf = set()
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
    def add_makefile (self, tmp) :
        with (tmp / "Makefile").open("w") as make :
            make.write("all:"
                       "\n\t"
                       f"@echo -e '{self.CFG.COW.GCC_BANNER}'"
                       "\n")
            obj_files = []
            for path in self.source :
                cf = self._cf[path]
                objpath = path.with_suffix(".o")
                obj_files.append(str(objpath))
                # see https://airbus-seclab.github.io/c-compiler-security/gcc_compilation.html
                make.write("\t"
                           f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                           "\n\t"
                           f"gcc -c -g -fno-inline -fno-omit-frame-pointer -std=c11"
                           f" -Wall -Wpedantic -Wextra {' '.join(cf)}"
                           f" -Wformat=2 -Wformat-overflow=2 -Wformat-truncation=2"
                           f" -Wnull-dereference -Walloca -Wvla -Warray-bounds=2"
                           f" -Wstringop-overflow=4"
                           f" -Wconversion -Wint-conversion"
                           f" -Wlogical-op -Wduplicated-cond -Wduplicated-branches"
                           f" -Wformat-signedness "
                           f" -Wstrict-overflow=4"
                           f" -Wundef"
                           f" -Wswitch-default -Wswitch-enum"
                           f" {path} -o {objpath}"
                           "\n")
            make.write("\t"
                       f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                       "\n\t"
                       f"gcc {' '.join(obj_files)} {' '.join(self._lf)} -o a.out"
                       "\n\t"
                       f"@echo -e '{self.CFG.COW.RUN_BANNER}'"
                       "\n\t"
                       f"@echo -ne '{self.CFG.COW.MAKE_PROMPT}'"
                       "\n\t"
                       f"./a.out"
                       "\n")

class CoWzip (_CoWzip) :
    pass
