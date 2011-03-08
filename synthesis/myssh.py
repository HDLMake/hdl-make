# -*- coding: utf-8 -*-
import os

class MySSH:
    def __init__(self, ssh_user, ssh_server):
        self.ssh_user = ssh_user
        self.ssh_server = ssh_server
    def system(self, cmd):
        os.system("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')
    def popen(self, cmd):
        return os.popen("ssh " + self.ssh_user + "@" + self.ssh_server + ' "' + cmd + '"')