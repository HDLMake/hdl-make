"""Package containing the classes required to print a Makefile"""

from hdlmake.tools import (
    ToolIVerilog, ToolISim, ToolModelsim,
    ToolActiveHDL, ToolRiviera, ToolGHDL)

from hdlmake.tools import (
    ToolISE, ToolPlanAhead, ToolVivado,
    ToolQuartus, ToolDiamond, ToolLibero)


class WriterSim(object):

    """Class that is in charge of writing simulation Makefiles"""

    def __init__(self):
        self.iverilog = ToolIVerilog()
        self.isim = ToolISim()
        self.modelsim = ToolModelsim()
        self.active_hdl = ToolActiveHDL()
        self.riviera = ToolRiviera()
        self.ghdl = ToolGHDL()
        self.vivado = ToolVivado()

class WriterSyn(object):

    """Class that is in charge of writing synthesis Makefiles"""

    def __init__(self):
        self.ise = ToolISE()
        self.planahead = ToolPlanAhead()
        self.vivado = ToolVivado()
        self.quartus = ToolQuartus()
        self.diamond = ToolDiamond()
        self.libero = ToolLibero()


