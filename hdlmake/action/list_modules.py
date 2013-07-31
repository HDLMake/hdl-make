from action import Action
from util import path


class ListModules(Action):
    def run(self):
        for m in self.modules_pool:
            if not m.isfetched:
                print("#!UNFETCHED")
                print(m.url+'\n')
            else:
                print(path.relpath(m.path))
                if m.source in ["svn", "git"]:
                    print("# "+m.url)
                if m.parent:
                    print("# defined in %s" % m.parent.url)
                else:
                    print("# root module")
                if not len(m.files):
                    print("   # no files")
                else:
                    for f in m.files:
                        print("   " + path.relpath(f.path, m.path))
                print("")
