#include ../../../../../Makedefs
##user defined things
#-------------------------------------------------------------------------------------
PROJECT_PATH := /home/pawel/wrdev
SCRIPTS_PATH := $(PROJECT_PATH)/scripts
HDL_PATH := $(PROJECT_PATH)/hdl
#				_	
#do NOT change below this line	|	
#				v
#--------------------------------------------------------------------------------------

##variables
DEPEND_FILE := dependencies.mk
PWD := $(shell pwd)
WORK_NAME := work
WORK_PATH := $(PWD)/$(WORK_NAME)

MODELSIM_INI_PATH := /opt/modeltech

VCOM_FLAGS := -nologo -quiet -93 -modelsimini ./modelsim.ini
VSIM_FLAGS := -voptargs="+acc"
VLOG_FLAGS := +incdir+../../../../sim/fabric_emu_new +incdir+../../../../sim \
-nologo -quiet -sv -modelsimini $(PWD)/modelsim.ini

VHDL_SRC:=$(shell $(SCRIPTS_PATH)/sources.sh $(HDL_PATH) $(SCRIPTS_PATH))
#VHDL_OBJ is defined in $(DEPEND_FILE)
#LIBS is defined in $(DEPEND_FILE)
SV_SRC := $(wildcard $(PWD)/*.sv)
SV_OBJ:=$(foreach svfile, $(SV_SRC), $(WORK_PATH)/$(patsubst %.sv,%/_primary.dat,$(notdir $(svfile))))

##rules
all: modelsim.ini $(LIB_IND) $(DEPEND_FILE) $(SV_OBJ) $(VHDL_OBJ)
$(DEPEND_FILE): $(VHDL_SRC)
	@echo 'Creating dependencies file..'
	@echo $(VHDL_SRC)|$(SCRIPTS_PATH)/sources-lib.sh $(HDL_PATH) $(SCRIPTS_PATH) |$(SCRIPTS_PATH)/vhdldep.sh $(SCRIPTS_PATH) "vcom $(VCOM_FLAGS)"$ > $(DEPEND_FILE)
include $(DEPEND_FILE)

$(SV_OBJ): $(VHDL_OBJ) 
$(VHDL_OBJ): $(LIB_IND) modelsim.ini
#LIBS: modelsim.ini

$(WORK_PATH)/%/_primary.dat: %.sv
	vlog -work $(WORK_PATH) $(VLOG_FLAGS) $<

modelsim.ini: $(MODELSIM_INI_PATH)/modelsim.ini
	cp $< .

clean:
	rm -rf ./modelsim.ini $(LIBS) $(LIB_IND) $(DEPEND_FILE)
	
.PHONY: clean
