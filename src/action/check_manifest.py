from action import Action
from manifest_parser import ManifestParser


class CheckManifest(Action):
    def _check_options(self):
        if not self.options.top:
            logging.info("--top is not specified. Current manifest will be treated as the top manifest")

    def run(self):
        ###
        ### THIS IS JUST A STUB
        ###
        manifest_parser = ManifestParser()

        manifest_parser.add_arbitrary_code("__manifest=\""+self.path+"\"")
        manifest_parser.add_arbitrary_code(global_mod.options.arbitrary_code)

        opt_map = manifest_parser.parse()
