#!/usr/bin/env python
from action import Action


class ListFiles(Action):
    def run(self):
        files_str = []
        for m in self.modules_pool:
            if not m.isfetched:
                continue
            files_str.append(self.options.delimiter.join([f.path for f in m.files]))
        print(" ".join(files_str))
