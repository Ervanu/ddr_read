from migen import *
from litex.soc.interconnect import stream
from migen.fhdl import verilog

class VideoTestPattern(Module):
    def __init__(self):
        self.source = source = stream.Endpoint([("data", 24),("vdal", 1),("vvap", 1)])
        row_cnt   = Signal(11)
        v_count   = Signal(10)
        y  = Signal(8)  
        cb = Signal(8)
        cr = Signal(8)
        # Logic to cycle through the components on every clock where data is accepted
        self.sync += [
            If(source.valid & source.ready,
                row_cnt.eq(row_cnt + 1),
                If(row_cnt == 720,
                    row_cnt.eq(0),   
                    v_count.eq(Mux(v_count == 575,0,v_count +1))
                )
            )
        ]
        # Combinatorial output logic
        self.comb += [
            source.valid.eq(1),
            # Horizontal pixel color test
            If((row_cnt < 179),  y.eq(82), cb.eq(90),cr.eq(240)),
            If((row_cnt >  179),  y.eq(120), cb.eq(54),cr.eq(34)),
            If((row_cnt > 359),  y.eq(82), cb.eq(90),cr.eq(240)),
            If((row_cnt >  539),  y.eq(120), cb.eq(54),cr.eq(34)),

            # vertical pixel color test
            # If((v_count >= 0)
            #     , y.eq(82), cb.eq(90),cr.eq(240)),
            # If((v_count >= 144)
            #     , y.eq(243), cb.eq(128),cr.eq(128)),
            # If((v_count >= 288)
            #     , y.eq(82), cb.eq(90),cr.eq(240)),
            # If((v_count >= 432)
            #     , y.eq(243), cb.eq(128),cr.eq(128)),       
            source.data.eq((y << 16)+(cb << 8)+ cr)
        ]