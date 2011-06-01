SRC := configparser.py connection.py dep_solver.py fetch.py\
flow.py global_mod.py hdlmake_kernel.py helper_classes.py\
__main__.py makefile_writer.py module.py msg.py path.py\
 srcfile.py

ARCH := hdlmake

../$(ARCH): $(SRC)
	zip $(ARCH) $(SRC)
	mv $(ARCH).zip ../$(ARCH)
	chmod +x ../$(ARCH)

push: ../$(ARCH) $(SRC)
	cd .. && git push && cd src				
