from migen import *
from litex.soc.interconnect import wishbone, stream
from modules.wishbone_dma.wishboneDMA import WishboneDMAReader
from litex.soc.interconnect.csr import CSRStorage, CSRStatus, AutoCSR
# class StreamSink(Module):
#     def __init__(self):
#         self.sink = stream.Endpoint([("data", 32)])
#         self.comb += self.sink.ready.eq(1)

# class WishboneDMATest(Module):
#     def __init__(self):
#         # Instantiate DMA reader
#         self.submodules.dma = dma = WishboneDMAReader()

#         # Control signals for test
#         self.start = Signal()
#         self.done  = Signal()
#         self.data  = Signal(32)

#         # Connect control signals
#         self.comb += [
#             dma.start.eq(self.start),
#             self.done.eq(dma.done),
#         ]

#         # Capture output data from stream
#         self.sync += [
#             If(dma.source.valid,
#                 If(dma.source.ready,
#                     self.data.eq(dma.source.data)
#                 )
#             )
#         ]

#         # For this test, hardcode DMA to read **1 word from address 0**
#         self.comb += [
#             dma.base_addr.eq(0),
#             dma.length.eq(1),
#             dma.source.ready.eq(1)  # always ready to accept data
#         ]
#
class WishboneDMATest(Module, AutoCSR):
    def __init__(self):
        # CSRs
        self.start     = CSRStorage()  # no pulse argument
        self.done      = CSRStatus()
        self.data      = CSRStatus(32)

        self.base_addr = CSRStorage(32)
        self.length    = CSRStorage(32)

        # DMA Reader
        self.submodules.dma = dma = WishboneDMAReader()

        # detect rising edge of start
        start_r = Signal()
        pulse   = Signal()

        self.sync += [
            start_r.eq(self.start.storage),
            pulse.eq(self.start.storage & ~start_r)  # 1-cycle pulse
        ]

        # Connect CSRs to DMA
        self.comb += [
            dma.start.eq(pulse),
            dma.base_addr.eq(self.base_addr.storage),
            dma.length.eq(self.length.storage),
            self.done.status.eq(dma.done),
            self.data.status.eq(dma.source.data),
        ]