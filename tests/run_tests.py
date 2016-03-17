# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 CERN
# Author: Joshua Smith (joshrsmith@gmail.com)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import subprocess

def test_makefile_generation():
    """This simple function finds top level (action) manifest files based on an
    assumed directory structure and attempts to run hdlmake on them. If hdlmake
    exits with a successful exit code, it assumes hdlmake was successful.
        
    This is more of an exercise of the code than a check for Makefile correctness. 
        
    Assumes python is on the $PATH
    """
    this_mod_dir = os.path.dirname(__file__)
    failures = []
    # Get the absolute path to the hdlmake base project directory, and put it on
    # a copied environment's PYTHONPATH. This will later allow us to execute the
    # package as a script using "-m" option to python
    hdlmakedir = os.path.abspath(os.path.join(this_mod_dir,'..'))
    subprocess_env = os.environ.copy()
    if "PYTHONPATH" in subprocess_env:
        subprocess_env["PYTHONPATH"] = hdlmakedir + ":" + subprocess_env["PYTHONPATH"]
    else:
        subprocess_env["PYTHONPATH"] = hdlmakedir
        
    manifests_locations = []
    
    for action in ('sim','syn'):  # currently only works on sim. The force option does not appear to work on syn targets
        for (dirname, subdir_items, filelist) in os.walk(os.path.join(this_mod_dir,'counter',action)):
            for filename in filelist:
                if "Manifest.py" in filename:
                    print "Found: " + os.path.join(dirname,filename)
                    manifests_locations.append(os.path.abspath(dirname))
                    
    print "Running hdlmake on found manifests..."
    
    for manifestdir in manifests_locations:
        
        os.chdir(manifestdir)
        args = ["python",
                "-m", 
                "hdlmake",
                "auto",
                "--force"]
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            print "Error processing manifest in: " + manifestdir
            failures.append(manifestdir)
    
    if len(failures) > 0:
        print "Problems processing the following Manifest files:"
        for failure in failures:
            print failure
    else:
        print "Successfully processed all Manifest files."

def main():
    test_makefile_generation()

if __name__ == "__main__":
    main()
    