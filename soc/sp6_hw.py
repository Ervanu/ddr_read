#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2019 Michael Betz <michibetz@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.xilinx import *
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxSpartan6Platform
from litex.build.openfpgaloader import OpenFPGALoader


# from litex.build.io import DDROutput

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk50", 0, Pins("A10"), IOStandard("LVCMOS33")),
    # ("cpu_reset", 0, Pins("T11"), IOStandard("LVCMOS33")),
    

    # Leds
    # ("user_led", 0, Pins("T9 T14 T15 R16 P16 L13 M14 M16"), IOStandard("LVCMOS33")),
    # ("user_led", 0, Pins("T9"), IOStandard("LVCMOS33")),
    ("led1", 0, Pins("T9"), IOStandard("LVCMOS33")),
    ("led2", 0, Pins("R9"), IOStandard("LVCMOS33")),
    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("E13")),
        Subsignal("rx", Pins("B16")),
        IOStandard("LVCMOS33")
    ),
    # uart PL
    ("uart_pl", 0,
        Subsignal("tx", Pins("E12")),
        Subsignal("rx", Pins("B15")),
        IOStandard("LVCMOS33")
    ),
     #I2C adv7391 video encoder
    ("i2c", 0,
        Subsignal("scl", Pins("J11"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("M15"), IOStandard("LVCMOS33"))
    ),
    ("adv7391_rst", 0, Pins("K11"), IOStandard("LVCMOS33")),
    ("adv7391_llc", 0, Pins("K14"), IOStandard("LVCMOS33")),
    ("adv7391", 0,
        Subsignal("d", Pins("T12 T13 R14 R15 P15 L12 M13 N14")),
        IOStandard("LVCMOS33")
    ),
    # DDR3 SDRAM
    # MT41K128M16JT-125K
     ("ddram_clock", 0,
        Subsignal("p", Pins("E2")),
        Subsignal("n", Pins("E1")),
        IOStandard("DIFF_SSTL15_II"), Misc("IN_TERM=NONE")
    ),
    ("ddram", 0,
        Subsignal("a", Pins(
            "K5 K6 D1 L4 G5 H4 H3 D3 B2 A2 G6 E3 F3 F6 F5"),
            IOStandard("SSTL15_II")),
        Subsignal("ba", Pins("C3 C2 B1"), IOStandard("SSTL15_II")),
        Subsignal("ras_n", Pins("J6"), IOStandard("SSTL15_II")),
        Subsignal("cas_n", Pins("H5"), IOStandard("SSTL15_II")),
        Subsignal("we_n",  Pins("C1"), IOStandard("SSTL15_II")),

        # cs_n hardwired on board

        Subsignal("dm", Pins("J4 K3"), IOStandard("SSTL15_II")),

        # DATA (NO IN_TERM!)
        Subsignal("dq", Pins(
            "G3 J3 G1 K1 F1 K2 F2 J1 R1 M2 R2 L3 P1 L1 P2 M1"),
            IOStandard("SSTL15_II")),

        # DQS (NO IN_TERM!)
        Subsignal("dqs", Pins("H2 N3"),
            IOStandard("DIFF_SSTL15_II")),
        Subsignal("dqs_n", Pins("H1 N1"),
            IOStandard("DIFF_SSTL15_II")),

        # CLOCK MUST BE DIFFERENTIAL
        # Subsignal("ck_p", Pins("E2"), IOStandard("DIFF_SSTL15_II")),
        # Subsignal("ck_n", Pins("E1"), IOStandard("DIFF_SSTL15_II")),
        # Subsignal("ck", Pins("E2 E1"), IOStandard("SSTL15_II")),
        Subsignal("cke", Pins("F4"), IOStandard("SSTL15_II")),
        Subsignal("odt", Pins("L5"), IOStandard("SSTL15_II")),
        Subsignal("reset_n", Pins("E4"), IOStandard("SSTL15_II")),

        Misc("SLEW=FAST"),
    ),
    # SPIFlash (W25Q128JV)
    ("spiflash", 0,
        Subsignal("cs_n", Pins("T3"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("R11"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("P10"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("T10"), IOStandard("LVCMOS33")),
    ),

]

 #Platform -----------------------------------------------------------------------------------------

class Platform(XilinxSpartan6Platform):
    default_clk_name   = "clk50"
    # default_clk_period = 1e9/50e6
    #xc6slx25-3n-ftg256
    def __init__(self, toolchain="ise", **kwargs):
        XilinxSpartan6Platform.__init__(self, "xc6slx25-3n-ftg256", _io, toolchain=toolchain) #xc6slx25tcsg324
        self.add_platform_command("NET \"*\" CLOCK_DEDICATED_ROUTE = FALSE;")
        self.toolchain.additional_commands = ["write_bitstream -force -bin_file {build_name}"]

    def create_programmer(self, kit="openfpgaloader"):
        return OpenFPGALoader(cable="dirtyJtag")

    def do_finalize(self, fragment):
        XilinxSpartan6Platform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk50", loose=True), 1e9/50e6)