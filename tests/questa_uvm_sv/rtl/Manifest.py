include_dirs = "./include"

files = ["include/includeModuleSV.sv",
         "include/includeModuleVHDL.vhdl",
         "include/includeModuleAVHDL.vhdl",
         "include/includeModuleBVHDL.vhdl",
         "RTL_SVPackage.sv",
         "RTLTopModuleSV.sv",
         "RTLTopModuleVerilogSimulationModel.vo",
         "RTLTopModuleVHDL.vhdl"]

modules = { "local" : ["../ipcores/ipcore"]}
