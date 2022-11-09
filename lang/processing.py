import re
from pathlib import Path

from . import CoWrunX as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    _ide_opt = re.compile(r"^//\s*(ide)\s*$", re.I|re.M)
    def add_source (self, tmp, path, text) :
        if getattr(self, "sketchbook", None) is None :
            self.sketchbook = Path(path.stem)
            (tmp / self.sketchbook).mkdir(parents=True, exist_ok=True)
        super().add_source(tmp, self.sketchbook / path, text)
        for match in self._ide_opt.findall(text) :
            self.make = f"processing {self.sketchbook}/{self.sketchbook}.pde"
    def add_makefile (self, tmp) :
        cmd = f"{self.CFG.LANG.PROCESSING.CMD} --sketch={self.sketchbook} --run"
        with (tmp / "run.sh").open("w", encoding="utf-8", errors="replace") as run :
            run.write(f"echo -e '{self.CFG.COW.RUN_BANNER}'\n"
                      f"echo -e '{self.CFG.COW.MAKE_PROMPT} {cmd}'\n"
                      f"{cmd}\n"
                      f"STATUS=$?\n"
                      f"echo -e '{self.CFG.COW.END_BANNER}'\n"
                      f"read\n"
                      f"exit $STATUS\n")
        with (tmp / "Makefile").open("w", encoding="utf-8", errors="replace") as make :
            make.write("all:\n"
                       "\t@bash run.sh\n")

class CoWzip (_CoWzip) :
    def items (self, project) :
        sketchbook = None
        for path, data in project.items() :
            if sketchbook is None :
                sketchbook = Path(path.stem)
            yield sketchbook / path, data
