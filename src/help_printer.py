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

import msg as p

class HelpPrinter():
    @staticmethod
    def print_action_help():
        p.rawprint("`Action' variable was not specified")
        p.rawprint("Allowed values are: \"simulation\" or \"synthesis\"")
        p.rawprint()
        p.rawprint("This variable in a manifest file is necessary for Hdlmake " \
        "to be able to know what to do with the given modules' structure.")
        HelpPrinter.__more()

    @staticmethod
    def __more():
        p.rawprint("For more help type `hdlmake --help' " \
        "or visit http://www.ohwr.org/projects/hdl-make")

if __name__ == "__main__":
    hp = HelpPrinter
    hp.print_action_help()