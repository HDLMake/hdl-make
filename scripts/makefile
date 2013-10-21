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
SRC_DIR := ../hdlmake
SRC_FILES := $(shell find $(SRC_DIR) -name '*py')
SRC_FILES_BASENAMES = $(foreach src, $(SRC_FILES), $(shell basename $(src)))

TAG = $(shell cd .. && git describe --abbrev=0 --tags --always)#get the latest tag
RELEASE = hdlmake-$(TAG).tar.gz
ARCH := hdlmake$(TAG)

single_file_app: warning $(ARCH)
$(ARCH): $(SRC_FILES)
	bash build_hash.sh
	cd $(SRC_DIR) &&\
	zip $(ARCH) build_hash.py $(SRC_FILES_BASENAMES) &&\
	echo '#!/usr/bin/python' > $(ARCH) &&\
	cat $(ARCH).zip >> $(ARCH) &&\
	rm $(ARCH).zip &&\
	chmod +x $(ARCH) &&\
	mv $(ARCH) ..

release: $(RELEASE)
$(RELEASE): $(ARCH) $(SRC)
	tar -zcvf $@ *

warning:
	echo This makefile is not ment to build an executable file.
	echo The default way to run hdlmake is to give the path
	echo to the source code as the first argument to the Python
	echo interpreter call, for instance:
	echo python path/to/hdl-make/hdlmake
	echo If you _really_ need to have a single file, then
	echo you might use this makefile, but in some cases it might
	echo reduce the volume of displayed debugging information.
	sleep 5

.PHONY: clean

clean:
	rm -f $(SRC_DIR)/*~ $(SRC_DIR)/*pyc ../$(ARCH) ../hdlmake-*.tar.gz 

