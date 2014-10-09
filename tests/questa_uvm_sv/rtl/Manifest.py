include_dirs = "./include"

files = ["include/includeModule.sv",
         "RTL_SVPackage.sv",
         "RTLTopModuleSV.sv",
         "RTLTopModuleVerilogSimulationModel.vo",
         "RTLTopModuleVHDL.vhdl"]

modules = { "local" : ["../ipcores/ipcore"]}
