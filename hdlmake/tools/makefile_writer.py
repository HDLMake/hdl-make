"""Module providing the synthesis functionality for writing Makefiles"""


import logging

def load_syn_tool(tool_name):
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
    if tool_name in available_tools:
        logging.debug("Synthesis tool to be used found: %s", tool_name)
        return available_tools[tool_name]()
    else:
        logging.error("Unknown synthesis tool: %s", tool_name)
        quit()


def load_sim_tool(tool_name):
    """Funtion that checks the provided module_pool and generate an
    initialized instance of the the appropriated simulation tool"""
    from .iverilog import ToolIVerilog
    from .isim import ToolISim
    from .modelsim import ToolModelsim
    from .active_hdl import ToolActiveHDL
    from .riviera import ToolRiviera
    from .ghdl import ToolGHDL
    from .vivado_sim import ToolVivadoSim
    available_tools = {'iverilog': ToolIVerilog,
                       'isim': ToolISim,
                       'modelsim':  ToolModelsim,
                       'active_hdl': ToolActiveHDL,
                       'riviera':  ToolRiviera,
                       'ghdl': ToolGHDL,
                       'vivado_sim': ToolVivadoSim}
    if tool_name in available_tools:
        logging.debug("Simulation tool to be used found: %s", tool_name)
        return available_tools[tool_name]()
    else:
        logging.error("Unknown simulation tool: %s", tool_name)
        quit()
