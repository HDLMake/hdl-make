from .. common.sim_makefile_support import VsimMakefileWriter

class ToolControls(VsimMakefileWriter):
    def __init__(self):
        super(ToolControls, self).__init__()

    def detect_version(self, path):
        pass

    def get_keys(self):
        tool_info = {
            'name': 'No Tool',
            'id': 'notool',
            'windows_bin': '',
            'linux_bin': ''
        }
        return tool_info

    def get_standard_libraries(self):
        return ["ieee", "std", "altera_mf"]

    def generate_simulation_makefile(self, fileset, top_module):
        pass
