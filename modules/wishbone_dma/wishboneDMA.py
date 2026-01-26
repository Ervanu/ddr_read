from migen import *
from litex.soc.interconnect import wishbone, stream


class WishboneDMAReader(Module):
    def __init__(self):
        self.bus = wishbone.Interface()
        self.source = stream.Endpoint([("data", 32)])

        self.base_addr = Signal(32)
        self.length    = Signal(32)
        self.start     = Signal()
        self.busy      = Signal()
        self.done      = Signal()

        addr  = Signal(32)
        count = Signal(32)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm

        fsm.act("IDLE",
            self.busy.eq(0),
            self.done.eq(0),
            If(self.start,
                NextValue(addr, self.base_addr),
                NextValue(count, self.length),
                NextState("READ")
            )
        )

        fsm.act("READ",
            self.busy.eq(1),
            self.bus.cyc.eq(1),
            self.bus.stb.eq(1),
            self.bus.we.eq(0),
            self.bus.adr.eq(addr[2:]),
            If(self.bus.ack,
                NextState("PUSH")
            )
        )

        fsm.act("PUSH",
            self.busy.eq(1),
            self.source.valid.eq(1),
            self.source.data.eq(self.bus.dat_r),
            If(self.source.ready,
                NextValue(addr, addr + 4),
                NextValue(count, count - 1),
                If(count == 1,
                    NextState("DONE")
                ).Else(
                    NextState("READ")
                )
            )
        )

        fsm.act("DONE",
            self.busy.eq(0),
            self.done.eq(1),
            If(~self.start,
                NextState("IDLE")
            )
        )
