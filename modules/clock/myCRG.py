from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *
from litex.soc.cores.clock import *
from litex.soc.cores.gpio import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.build.io import DDROutput
# from litedram.modules import MT41J128M16
# from litedram.phy import s6ddrphy, GENSDRPHY

# from litex.build.parser import LiteXArgumentParser


XTAL_VAL = 50e6

# CRG ----------------------------------------------------------------------------------------------
class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq):
        # Clock domains for the system (soft CPU and related components run at).
        self.cd_sys = ClockDomain("sys")
        # self.cd_sys   = ClockDomain()
        self.cd_sys2x = ClockDomain("sys2x")
        self.cd_c27m  = ClockDomain("c27m")

        # Clo the DDR interface.
        self.cd_sdram_half      = ClockDomain("sdram_half")
        self.cd_sdram_full_wr   = ClockDomain("sdram_full_wr")
        self.cd_sdram_full_rd   = ClockDomain("sdram_full_rd")
        self.unbuf_sdram_full   = ClockDomain("sdram_full")
        self.unbuf_sdram_half_a = ClockDomain("sdram_half_a")
        self.unbuf_sdram_half_b = ClockDomain("dram_half_b")

        # DVI clock domain
        # self.cd_dvi = ClockDomain()
        # self.cd_dvi90 = ClockDomain()

        # PLL signals
        clk50 = platform.request("clk50")
        self.pll = pll = S6PLL(speedgrade=-3)
        pll.register_clkin(clk50, XTAL_VAL)
        pll.create_clkout(self.unbuf_sdram_full, sys_clk_freq*8, with_reset=False, buf=None)
        pll.create_clkout(self.unbuf_sdram_half_a, sys_clk_freq*4, phase=230, with_reset=False, buf=None)
        pll.create_clkout(self.unbuf_sdram_half_b, sys_clk_freq*4, phase=210, with_reset=False, buf=None)
        pll.create_clkout(self.cd_sys2x, sys_clk_freq*2, with_reset=False)
        pll.create_clkout(self.cd_sys, sys_clk_freq, with_reset=False)

        # self.pll2 = pll2 = S6PLL()
        # pll2.register_clkin(clk50, XTAL_VAL)
        # pll2.create_clkout(self.cd_c27m,27e6)
        # SDRAM clocks
        # ------------------------------------------------------------------------------
        self.clk8x_wr_strb = Signal()
        self.clk8x_rd_strb = Signal()

        # sdram_full
        self.specials += Instance("BUFPLL",
                                  p_DIVIDE=4,
                                  i_PLLIN=self.unbuf_sdram_full.clk, i_GCLK=self.cd_sys2x.clk,
                                  i_LOCKED=pll.locked,
                                  o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk8x_wr_strb
                                  )
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk8x_rd_strb.eq(self.clk8x_wr_strb),
        ]

        # sdram_half
        self.specials += Instance("BUFG",
                                  i_I=self.unbuf_sdram_half_a.clk, 
                                  o_O=self.cd_sdram_half.clk
                                  )
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", 
                                  i_I=self.unbuf_sdram_half_b.clk, 
                                  o_O=clk_sdram_half_shifted
                                  )

        # sdram differential clock output
        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += DDROutput(1, 0, output_clk, clk_sdram_half_shifted)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)

        # video_clk_pin = platform.request("adv7391_llc")
        # self.specials += Instance("ODDR2",
        #     p_DDR_ALIGNMENT = "NONE",
        #     p_INIT          = 0,
        #     p_SRTYPE        = "SYNC",
        #     i_D0            = 1,
        #     i_D1            = 0,
        #     i_CE            = 1,
        #     i_C0            = ClockSignal("c27m"),
        #     i_C1            = ~ClockSignal("c27m"),
        #     i_R             = 0,
        #     i_S             = 0,
        #     o_Q             = video_clk_pin
        # )