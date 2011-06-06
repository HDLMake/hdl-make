#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import path

class ModulePool(list):
    class ModuleFetcher:
        def __init__(self):
            pass

        def fetch_single_module(self, module):
            new_modules = []
            p.vprint("Fetching manifest: " + str(module.manifest))

            if module.source == "local":
                p.vprint("ModPath: " + module.path);
            if module.source == "svn":
                p.vprint("[svn] Fetching to " + module.fetchto)
                self.__fetch_from_svn(module)
            if module.source == "git":
                p.vprint("[git] Fetching to " + module.fetchto)
                self.__fetch_from_git(module)

            module.parse_manifest()

            if module.root_module != None:
                p.vprint("Encountered root manifest: " + str(module.root_module))
                new_modules.append(module.root_module)

            new_modules.extend(module.local)
            new_modules.extend(module.svn)
            new_modules.extend(module.git)
            return new_modules 

        def __fetch_from_svn(self, module):
            fetchto = module.fetchto
            if not os.path.exists(fetchto):
                os.mkdir(fetchto)

            cur_dir = os.getcwd()
            os.chdir(fetchto)
            url, rev = self.__parse_repo_url(module.url)

            basename = path.url_basename(url)

            cmd = "svn checkout {0} " + basename
            if rev:
                cmd = cmd.format(url + '@' + rev)
            else:
                cmd = cmd.format(url)

            rval = True

            p.vprint(cmd)
            if os.system(cmd) != 0:
                rval = False
            os.chdir(cur_dir)

            module.isfetched = True
            module.revision = rev
            module.path = os.path.join(fetchto, basename)
            return rval

        def __fetch_from_git(self, module):
            fetchto = module.fetchto
            if not os.path.exists(fetchto):
                os.mkdir(fetchto)

            cur_dir = os.getcwd()
            os.chdir(fetchto)
            url, rev = self.__parse_repo_url(module.url)

            basename = path.url_basename(url)

            if basename.endswith(".git"):
                basename = basename[:-4] #remove trailing .git

            if not os.path.exists(os.path.join(fetchto, basename)):
                update_only = False
            else:
                update_only = True

            if update_only:
                cmd = "git --git-dir="+basename+"/.git pull"
            else:
                cmd = "git clone " + url

            rval = True

            p.vprint(cmd)
            if os.system(cmd) != 0:
                rval = False

            if rev and rval:
                os.chdir(basename)
                cmd = "git checkout " + rev
                p.vprint(cmd)
                if os.system(cmd) != 0:
                    rval = False

            os.chdir(cur_dir)
            module.isfetched = True
            module.revision = rev
            module.path = os.path.join(fetchto, basename)
            return rval

        def __parse_repo_url(self, url) :
            """
            Check if link to a repo seems to be correct. Filter revision number
            """
            import re
            url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
            url_match = re.match(url_pat, url)

            if url_match == None:
                p.echo("Not a correct repo url: {0}. Skipping".format(url))
            if url_match.group(3) != None: #there is a revision given 
                ret = (url_match.group(1), url_match.group(3))
            else:
                ret = (url_match.group(1), None)
            return ret
    #end class ModuleFetcher
    def __parse_repo_url(self, url) :
        """
        Check if link to a repo seems to be correct. Filter revision number
        """
        import re
        url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
        url_match = re.match(url_pat, url)

        if url_match == None:
            p.echo("Not a correct repo url: {0}. Skipping".format(url))
        if url_match.group(3) != None: #there is a revision given 
            ret = (url_match.group(1), url_match.group(3))
        else:
            ret = (url_match.group(1), None)
        return ret
    def __init__(self, top_module):
        self.top_module = top_module
        self.modules = []
        self.add(new_module=top_module)

    def __iter__(self):
        return self.modules.__iter__()

    def __len__(self):
        return len(self.modules)

    def __contains__(self,v):
        return v in self.modules

    def __getitem__(self,v):
        return self.modules[v]

    def __str__(self):
        return str([str(m) for m in self.modules])

    def __contains(self, module):
        for mod in self.modules:
            if mod.url == module.url:
                return True
        return False

    def add(self, new_module):
        from module import Module
        if not isinstance(new_module, Module):
            raise RuntimeError("Expecting a Module instance")
        if self.__contains(new_module):
            return
        if new_module.isfetched:
            for mod in new_module.submodules():
                self.add(mod)
        self.modules.append(new_module)
        return True

    def fetch_all(self):
        fetcher = self.ModuleFetcher()
        fetch_queue = [mod for mod in self.modules if not mod.isfetched]

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            new_modules = fetcher.fetch_single_module(cur_mod)

            for mod in new_modules:
                if not self.__contains(mod):
                    fetch_queue.append(mod)
                else:
                    pass

    def build_global_file_list(self):
        return self.top_module.build_global_file_list()

    def build_very_global_file_list(self):
        from srcfile import SourceFileFactory, VerilogFile
        sff = SourceFileFactory()

        files = self.top_module.build_global_file_list()
        extra_verilog_files = set() 
        queue = files.filter(VerilogFile)

        while len(queue) > 0:
            vl = queue.pop()
            extra_verilog_files.add(vl)
            for f in vl.dep_requires:
                nvl = sff.new(os.path.join(vl.dirname, f))
                if f not in extra_verilog_files and f not in files:
                    queue.append(nvl)

        p.vprint("Extra verilog files, not listed in manifests:")
        for file in extra_verilog_files:
            p.vprint(str(file))
        for file in extra_verilog_files:
            files.add(file)
        return files

    def get_top_module(self):
        return self.top_module

    def is_everything_fetched(self):
        for mod in self.modules:
            if mod.is_fetched_recursively() == False:
                return False
        return True
