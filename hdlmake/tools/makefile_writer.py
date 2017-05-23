"""Module providing the synthesis functionality for writing Makefiles"""


import logging

def _load_syn_tool(modules_pool):
    """Funtion that checks the provided module_pool and generate an
    initialized instance of the the appropriated synthesis tool"""
    from .ise import ToolISE
    from .planahead import ToolPlanAhead
    from .vivado import ToolVivado
    from .quartus import ToolQuartus
    from .diamond import ToolDiamond
    from .libero import ToolLibero
    from .icestorm import ToolIcestorm
    available_tools = {'ise': ToolISE,
                       'planahead':  ToolPlanAhead,
                       'vivado': ToolVivado,
                       'quartus': ToolQuartus,
                       'diamond': ToolDiamond,
                       'libero': ToolLibero,
                       'icestorm': ToolIcestorm}
    for mod in modules_pool:
        if 'syn_tool' in mod.manifest_dict:
            tool_name = mod.manifest_dict['syn_tool']
            if tool_name in available_tools:
                logging.debug("Tool to be used found: %s", tool_name)
                return available_tools[tool_name]()
    logging.error("Unknown synthesis tool: %s", tool_name)
    quit()


def _load_sim_tool(modules_pool):
    """Funtion that checks the provided module_pool and generate an
    initialized instance of the the appropriated simulation tool"""
    from .iverilog import ToolIVerilog
    from .isim import ToolISim
    from .modelsim import ToolModelsim
    from .active_hdl import ToolActiveHDL
    from .riviera import ToolRiviera
    from .ghdl import ToolGHDL
    from .vivado import ToolVivado
    available_tools = {'iverilog': ToolIVerilog,
                       'isim': ToolISim,
                       'modelsim':  ToolModelsim,
                       'active_hdl': ToolActiveHDL,
                       'riviera':  ToolRiviera,
                       'ghdl': ToolGHDL,
                       'vivado': ToolVivado}
    manifest_dict = modules_pool.get_top_module().manifest_dict
    tool_name = manifest_dict['sim_tool']
    if tool_name in available_tools:
        return available_tools[tool_name]()
    else:
        logging.error("Unknown simulation tool: %s", tool_name)
        quit()


def write_makefile(modules_pool):
    """Function that detects the appropriated tool and write the Makefile"""
    manifest_project_dict = modules_pool.get_config_dict()
    action = manifest_project_dict.get('action')
    if action == "simulation":
        sim_writer = _load_sim_tool(modules_pool)
        sim_writer.simulation_makefile(modules_pool)
    elif action == "synthesis":
        syn_writer = _load_syn_tool(modules_pool)
        syn_writer.synthesis_makefile(modules_pool)
    else:
        logging.error("Unknown requested action: %s", action)
        quit()

