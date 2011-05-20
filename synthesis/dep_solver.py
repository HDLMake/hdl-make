# -*- coding: utf-8 -*-
import msg as p


class IDependable:
    def __init__(self):
        self.dep_fixed = False;
        self.dep_index = 0;
        self.dep_provides = [];
        self.dep_requires = [];
        self.dep_depends_on = [];

class DependencySolver:
    def __init__(self):
        self.entities = {};

    def _lookup_post_provider(self, files, start_index, requires):
        while True:
            start_index = start_index + 1
            try:
                f = files[start_index];
            except IndexError:
                break

            if requires:
                for req in requires:
                    if req in f.dep_provides: 
                        return start_index
        return None

    def _find_provider_file(self, files, req):
        for f in files:
            if f.dep_provides:
                if req in f.dep_provides:
                    return f;

        return None

    def solve(self, fileset):
        n_iter = 0
        max_iter = 100
        import copy

        fset = fileset.files;

        f_nondep = []

        done = False
        while not done and (n_iter < max_iter):
            n_iter = n_iter+1
            done = True
            for f in fset:
                if not f.dep_fixed:
                    idx = fset.index(f)
                    k = self._lookup_post_provider(fset, idx, f.dep_requires);

                    if k:
                        done = False
                        fset[idx] = (fset[idx], fset[k])
                        fset[k] = fset[idx][0]
                        fset[idx] = fset[idx][1]

        if(n_iter == max_iter):
            p.rawprint("Maximum number of iterations reached when trying to solve the dependencies."+
            "Perhaps a cyclic inter-dependency problem...");
            return None

        for f in fset:
            if f.dep_fixed:
                f_nondep.append(copy.copy(f))
                del f
        

        f_nondep.sort(key=lambda f: f.dep_index)

        for f in fset:
            p.vprint(f.path)
            if f.dep_requires:
                for req in f.dep_requires:
                    pf = self._find_provider_file(fset, req)
                    if not pf:
                        p.rawprint("Missing dependency in file "+str(f)+": " + req)
                        quit()
                    else:
                        p.vprint("--> " + pf.path);
                        f.dep_depends_on.append(pf)

        import srcfile as sf


        newobj = sf.SourceFileSet();
        newobj.add(f_nondep);
        for f in fset:
            if not f.dep_fixed:
                newobj.add(f)

        for k in newobj.files:
            p.vprint(str(k.dep_index) + " " + k.path + str(k.dep_fixed))
        return newobj
                
            
