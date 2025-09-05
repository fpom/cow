import re
import shlex
from . import CoWrun as _CoWrun, CoWzip as _CoWzip


class CoWrun(_CoWrun):
    _run_opt = re.compile(r"^\#\s*run\s*:\s*(.+)$", re.I | re.M)
    _pip_opt = re.compile(r"^\#\s*pip\s*:\s*(.+)$", re.I | re.M)

    def add_source(self, tmp, path, text):
        super().add_source(tmp, path, text)
        if getattr(self, "main", None) is None:
            self.main = path
        for match in self._run_opt.findall(text):
            self.make = match.strip()
        self.pip = []
        for match in self._pip_opt.findall(text):
            self.pip.extend(shlex.split(match.strip()))

    def add_makefile(self, tmp):
        if re.search(r"\buv\s+run\b", self.CFG.LANG.PYTHON.CMD):
            with_pip = [f"--with {s}" for p in self.pip if (s := p.strip())]
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make:
            make.write(
                "all:\n"
                f"\t@echo -e '{self.CFG.COW.RUN_BANNER}'\n"
                f"\t@echo -ne '{self.CFG.COW.MAKE_PROMPT}'\n"
                f"\t{self.CFG.LANG.PYTHON.CMD} {' '.join(with_pip)} {self.main}\n"
            )


class CoWzip(_CoWzip):
    pass
