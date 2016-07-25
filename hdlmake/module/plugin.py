class ModulePlugin(object):

    def __init__(self):
        self.manifest = None
        self.manifest_dict = None

    def process_manifest(self):
        pass

    @staticmethod
    def flatten_list(sth):
        """Convert the argument in a list, being an empty list if none"""
        if sth is not None:
            if not isinstance(sth, (list, tuple)):
                sth = [sth]
        else:
            sth = []
        return sth


