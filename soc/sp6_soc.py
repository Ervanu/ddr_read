from .import sp6_hw
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.gen import *
from litei2c import LiteI2C
from litex.soc.cores.clock import *
from litex.soc.cores.gpio import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litedram.modules import MT41J128M16
from litedram.phy import s6ddrphy
from litex.build.parser import LiteXArgumentParser
from litex.soc.cores.uart import UARTPHY
from modules.clock.myCRG import _CRG
from modules.video_encoder.encoder1 import BT656SyncGen
from modules.video_encoder.video_test_pattern import VideoTestPattern
from modules.uart_pl.uart_tx import UARTTX32Single
from modules.wishbone_dma.wishboneDMA import WishboneDMAReader
from modules.wishbone_dma.Fifo2VideoStream import WishboneDMATest
from litex.soc.interconnect import wishbone
from litespi.modules import W25Q80BV
from litex.soc.integration.soc import SoCRegion
from litespi.opcodes import SpiNorFlashOpCodes
from litex.soc.doc import generate_docs

kB = 1024
mB = 1024*kB


# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=50e6,**kwargs):
        platform = sp6_hw.Platform()
# CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq)
# SoCCore ----------------------------------------------------------------------------------
        kwargs.pop("integrated_sram_size", None)
        kwargs.pop("uart_fifo_depth", None)
        SoCCore.__init__(self, platform, sys_clk_freq, 
                         ident="LiteX SoC on SPARTAN6", 
                         bus_endianness = "little",
                         uart_fifo_depth         = 64,
                         integrated_sram_size = 0x4000, # 16KiB
                         **kwargs)
        # SPI Flash (for firmware storage)
        self.mem_map["spiflash"] = 0x20000000
        self.add_spi_flash(
            mode        = "1x",
            module      = W25Q80BV(
                default_read_cmd=SpiNorFlashOpCodes.READ_1_1_1
            ),
            with_master = True,
            clk_freq    = 25e6
        )
        self.add_constant("FLASH_BOOT_ADDRESS", 0x200D0000)
        self.add_memory_region("spiflash_app", 0x200D0008, 0x10000, type="cached+linker")
        self.add_memory_region("main_ram_app", 0x40000008, 0x10000, type="cached+linker")
# SDR DDRAM --------------------------------------------------------------------------------
        self.ddrphy = s6ddrphy.S6QuarterRateDDRPHY(
            pads                = platform.request("ddram"),
            rd_bitslip          = 0,
            wr_bitslip          = 4,
            dqs_ddr_alignment   = "C0" 
        )
        self.comb += [
            self.ddrphy.clk8x_wr_strb.eq(self.crg.clk8x_wr_strb),
            self.ddrphy.clk8x_rd_strb.eq(self.crg.clk8x_rd_strb),
        ]
        self.add_sdram(
            name    = "sdram",
            phy     = self.ddrphy,
            module  = MT41J128M16(sys_clk_freq, "1:4"),
        )
# UART PHY ----------------------------------------------------------------------
        # uart_pads = platform.request("uart_pl")
        # self.submodules.uart_phy = UARTPHY(
        #     pads=uart_pads,
        #     clk_freq=50e6,
        #     baudrate=115200
        # )
#adv7391 video encoder ----------------------------------------------------------
        # adv7391_rst_pin = platform.request("adv7391_rst")
        # self.submodules.adv7391 = ITU_RBT_656(adv7391_rst_pin)
#i2c ----------------------------------------------------------------------------
        # pad_i2c = platform.request("i2c", 0)
        # self.submodules.i2c = LiteI2C(pads=pad_i2c, sys_clk_freq=sys_clk_freq)
        # # #video encoder stream
        # video_pads = platform.request("adv7391") # Assuming this contains .clk and .d
        # # Instantiate modules
        # self.submodules.video_pattern = ClockDomainsRenamer("c27m")(VideoTestPattern())
        # self.submodules.video_sync    = ClockDomainsRenamer("c27m")(BT656SyncGen())
        # # Connect Pipeline: Pattern Source -> SyncGen Sink
        # self.comb += self.video_pattern.source.connect(self.video_sync.sink)
        # # Connect SyncGen Source -> Hardware Pins
        # self.comb += video_pads.d.eq(self.video_sync.source.data)
        

        

# Build --------------------------------------------------------------------------------------------
def main():    
    parser = LiteXArgumentParser(platform=sp6_hw.Platform, description="LiteX SoC on Spartan6.")
    parser.add_target_argument("--flash",           action="store_true",    help="Flash bitstream")
    parser.add_target_argument("--sys-clk-freq",    default=50e6,          help="System clock frequency.")
    args = parser.parse_args()

    soc = BaseSoC(
        toolchain           = args.toolchain,
        l2_cache_size       = 0,
        sys_clk_freq        = args.sys_clk_freq,
        **parser.soc_argdict
    )
    builder = Builder(soc, 
                      compile_gateware=True, 
                      compile_software=True, 
                      bios_console="full" 
                    #   bios_features=["csr"] 
                    )
    if args.build:
        builder.build(**parser.toolchain_argdict)
    
    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram", ext=".bit"))

    if args.flash:
        prog = soc.platform.create_programmer()
        prog.flash(0, builder.get_bitstream_filename(mode="flash", ext=".bit"), fpga_part="xc6slx25csg324")
    # generate_docs(soc,"build/doc")
if __name__ == "__main__":
    main()