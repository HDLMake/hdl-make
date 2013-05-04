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
SRC_FILES := configparser.py connection.py dep_solver.py fetch.py\
flow.py flow_altera.py global_mod.py hdlmake_kernel.py\
__main__.py makefile_writer.py manifest_parser.py module.py msg.py path.py \
srcfile.py vlog_parser.py new_dep_solver.py
SRC_DIR := src

SRC := $(foreach src, $(SRC_FILES), $(SRC_DIR)/$(src))
TAG = $(shell git describe --abbrev=0 --tags --always)#get the latest tag
RELEASE = hdlmake-$(TAG).tar.gz
EXEC := hdlmake

executable: $(EXEC)
$(EXEC): $(SRC)
	bash embed_build_id.sh
	cd $(SRC_DIR) &&\
	zip $(EXEC) build_hash.py $(SRC_FILES) &&\
	echo '#!/usr/bin/python' > $(EXEC) &&\
	cat $(EXEC).zip >> $(EXEC) &&\
	rm $(EXEC).zip &&\
	chmod +x $(EXEC) &&\
	mv $(EXEC) ..

release: $(RELEASE)
$(RELEASE): $(EXEC) $(SRC)
	tar -zcvf $@ *

.PHONY: clean

clean:
	rm -f $(SRC_DIR)/*~ $(PREFIX)/*pyc $(EXEC) hdlmake-*.tar.gz 

