# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#

import os
import random
import string
import msg as p

class Connection:
    def __init__(self, ssh_user, ssh_server):
        #if ssh_user == None:
        #    ssh_user = os.getenv("HDLMAKE_USER")
        self.ssh_user = ssh_user

        #if ssh_server == None:
        #    ssh_server = os.getenv("HDLMAKE_SERVER")
        self.ssh_server = ssh_server

    def __str__(self):
        return self.ssh_user + '@' + self.ssh_server

    def __data_given(self):
        return self.ssh_user != None and self.ssh_server != None

    def __check(self):
        if not self.__data_given():
            p.echo("Error: no data for connection given")
            quit()

    def system(self, cmd):
        return os.system("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')

    def popen(self, cmd):
        return os.popen("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')

    def transfer_files_forth(self, files, dest_folder):
        """
        Takes list of files and sends them to remote machine. Name of a directory, where files are put
        is returned
        """
        self.__check()
        #create a new catalogue on remote machine
        if dest_folder == None:
            dest_folder = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8)) 
        mkdir_cmd = 'mkdir -p ' + dest_folder 
        import msg as p
        p.vprint("Connecting to " + str(self) + " and creating directory " + dest_folder + ": " + mkdir_cmd)
        self.system(mkdir_cmd)

        #create a string with filenames
        from pipes import quote
        local_files_str = ' '.join(quote(file.path) for file in files)

        rsync_cmd = "rsync -Rav " + local_files_str + " " + self.ssh_user + "@" + self.ssh_server + ":" + dest_folder
        #rsync_cmd += " > /dev/null"
        p.vprint("Coping files to remote machine: "+rsync_cmd) 
        import subprocess
        p = subprocess.Popen(rsync_cmd, shell=True)
        os.waitpid(p.pid, 0)[1]
        return dest_folder

    def transfer_files_back(self, what, where):
        self.__check()
        rsync_cmd = "rsync -av " + self.ssh_user + "@" + self.ssh_server + ":" + what + ' ' + where
        p.vprint(rsync_cmd)
        os.system(rsync_cmd)

    def is_good(self):
        if self.system('echo \"\"') != 0:
            return 0
        else:
            return 1

    def check_address_length(self):
        p = self.popen("uname -a")
        p = p.readlines()
        if not len(p):
            p.echo("Checking address length failed")
            return None
        elif "i686" in p[0]:
            return 32
        elif "x86_64" in p[0]:
            return 64
        else:
            return None