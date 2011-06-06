SRC := configparser.py connection.py dep_solver.py fetch.py\
flow.py global_mod.py hdlmake_kernel.py helper_classes.py\
__main__.py makefile_writer.py module.py msg.py path.py\
srcfile.py

ARCH := hdlmake

../$(ARCH): check $(SRC)
	zip $(ARCH) $(SRC)
	echo '#!/usr/bin/python' > ../$(ARCH)
	cat $(ARCH).zip >> ../$(ARCH)
	rm $(ARCH).zip
	chmod +x ../$(ARCH)

push: ../$(ARCH) $(SRC)
	cd .. && git push && cd src				

check:
	pyflakes $(SRC)
clean:
	(test -f ../$(ARCH) && rm ../$(ARCH)) || true
	rm -f *~ *pyc
