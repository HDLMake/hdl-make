#!/usr/bin/env python


def get_standard_libraries():
    import global_mod
    import quartus
    import ise
    import modelsim
    import iverilog
    import isim

    tm = global_mod.top_module
    if tm.action == "simulation":
        if tm.sim_tool == "modelsim" or tm.sim_tool == "vsim":
            return modelsim.MODELSIM_STANDARD_LIBS
        elif tm.sim_tool == "isim":
            return isim.ISIM_STANDARD_LIBS
        elif tm.sim_tool == "iverilog":
            return iverilog.IVERILOG_STANDARD_LIBS
    else:
        if tm.syn_tool == "quartus":
            return quartus.QUARTUS_STANDARD_LIBS
        elif tm.syn_tool == "ise":
            return ise.ISE_STANDARD_LIBS
