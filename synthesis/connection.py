# -*- coding: utf-8 -*-
import os
import random
import string

class Connection:
    def __init__(self, ssh_user, ssh_server):
        self.ssh_user = ssh_user
        self.ssh_server = ssh_server

    def system(self, cmd):
        return os.system("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')

    def popen(self, cmd):
        return os.popen("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')

    def transfer_files_forth(self, files, dest_folder):
        """
        Takes list of files and sends them to remote machine. Name of a directory, where files are put
        is returned
        """
        if not isinstance(files, list):
            return None;

        ssh_cmd = "ssh " + self.ssh_user + "@" + self.ssh_server

        #create a new catalogue on remote machine
        if dest_folder == None:
            dest_folder = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8)) 

        mkdir_cmd = 'mkdir ' + dest_folder 
        import msg as p
        p.vprint("Connecting to " + ssh_cmd + " and creating directory " + dest_folder + ": " + mkdir_cmd)
        self.system(mkdir_cmd)

        #create a string with filenames
        from pipes import quote
        local_files_str = ' '.join(quote(os.path.abspath(x)) for x in files)

        rsync_cmd = "rsync -Rav " + local_files_str + " " + self.ssh_user + "@" + self.ssh_server + ":" + dest_folder 
        p.vprint("Coping files to remote machine: "+rsync_cmd) 
        import subprocess
        p = subprocess.Popen(rsync_cmd, shell=True)
        os.waitpid(p.pid, 0)[1]
        return dest_folder

    def transfer_files_back(self, dest_folder):
        rsync_cmd = "rsync -av " + self.ssh_user + "@" + self.ssh_server + ":" + dest_folder + ' /'
        p.vprint(rsync_cmd)
        os.system(rsync_cmd)

    def is_good(self):
        if self.system('echo \"\"') != 0:
            return 0
        else:
            return 1