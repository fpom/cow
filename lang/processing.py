from . import CoWrun as _CoWrun, CoWzip as _CoWzip

class CoWrun (_CoWrun) :
    pass

class CoWzip (_CoWzip) :
    def items (self, project) :
        sketchbook = None
        for path, data in project.items() :
            if sketchbook is None :
                sketchbook = Path(path.stem)
            yield sketchbook / path, data
