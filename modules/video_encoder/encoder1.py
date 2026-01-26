from migen import *
from litex.soc.interconnect import stream


class BT656SyncGen(Module):
    def __init__(self):
        # ---------------------------------------------------------------------
        # Interfaces
        # ---------------------------------------------------------------------
        self.sink   = sink   = stream.Endpoint([("data", 24),("vdal", 1),("vvap", 1)])  # YCbCr 4:2:2 (unused test pattern)
        self.source = source = stream.Endpoint([("data", 8)])

        # ---------------------------------------------------------------------
        # Counters
        # ---------------------------------------------------------------------
        h_count = Signal(11)   # 0 .. 1727
        v_count = Signal(10)   # 0 .. 624

        pixel_h     = Signal(10)
        pixel_ready = Signal()

        # ---------------------------------------------------------------------
        # Test pattern
        # ---------------------------------------------------------------------
        y  = Signal(8)
        cb = Signal(8)
        cr = Signal(8)
        YCbCr = Signal(24)

        # ---------------------------------------------------------------------
        # Status bits
        # ---------------------------------------------------------------------
        H = Signal()
        V = Signal()
        F = Signal()
        EAV = Signal()      # End active video
        H_BLANK = Signal()  # Horizontal blanking
        SAV = Signal()      # Start cctive video
        DAL = Signal()      # Horizontal active pixel
        VAP = Signal()      # Vertical active pixel
        pix_phase = Signal(3)
        row_cnt = Signal(10)

        # ---------------------------------------------------------------------
        # Counters
        # ---------------------------------------------------------------------
        self.sync += [
            If(h_count == 1727,
                h_count.eq(0),
                If(v_count == 624, v_count.eq(0))
                .Else(v_count.eq(v_count + 1))
            ).Else(
                h_count.eq(h_count + 1)
            )
        ]
        # _______________________________________________________________________
        # |___EAV CODE___|___H_Blanking___|_______SAV________|_______DAL________|
        #      0 - 3          4 - 283          284 - 287         288 - 1727
        # -----------------------------------------------------------------------
        self.comb += EAV.eq(h_count < 4)
        self.comb += H_BLANK.eq((h_count >= 4) & (h_count < 284))
        self.comb += SAV.eq((h_count >= 284) & (h_count < 288))
        self.comb += DAL.eq(h_count >= 288)
        self.comb += VAP.eq(((v_count >= 23) & (v_count < 311)) | ((v_count >= 336)&(v_count < 624)))
        # ---------------------------------------------------------------------
        # Horizontal / Vertical / Field timing (BT.656 PAL)
        # ---------------------------------------------------------------------
        self.comb += F.eq(v_count >= 312)
        self.comb += H.eq(EAV)
        self.comb += V.eq(~VAP)

        # ---------------------------------------------------------------------
        # XY byte (BT.656 parity correct)
        # ---------------------------------------------------------------------
        xy = Signal(8)
        self.comb += [
            xy[7].eq(1),
            xy[6].eq(F),
            xy[5].eq(V),
            xy[4].eq(H),
            xy[3].eq(~(V ^ H)),
            xy[2].eq(~(F ^ H)),
            xy[1].eq(~(F ^ V)),
            xy[0].eq(~(F ^ V ^ H)),
        ]

        # ---------------------------------------------------------------------
        # FSM: SAV / ACTIVE / EAV / HBLANK
        # ---------------------------------------------------------------------
        pix_en = Signal(2)
        self.submodules.fsm = fsm = FSM(reset_state="SEND_EAV_FF")
        # EAV: bytes 0–3
        fsm.act("SEND_EAV_FF",
            If(EAV, source.data.eq(0xff), NextState("SEND_EAV_00_1"))
        )
        fsm.act("SEND_EAV_00_1",
            If(EAV, source.data.eq(0x00),NextState("SEND_EAV_00_2"))
        )
        fsm.act("SEND_EAV_00_2",
            If(EAV, source.data.eq(0x00),NextState("SEND_EAV_XY"))
        )
        fsm.act("SEND_EAV_XY",
            If(EAV, source.data.eq(xy), NextState("H_BLANK"))
        )
        # Horizontal blanking: bytes 4–283
        fsm.act("H_BLANK",
            If(H_BLANK, source.data.eq(Mux(h_count[1], 0x80, 0x10))),
            If(h_count == 283, NextState("SEND_SAV_FF"))
        )
        # SAV: bytes 284-287
        fsm.act("SEND_SAV_FF",
            If(SAV, source.data.eq(0xff), NextState("SEND_SAV_00_1"))
        )
        fsm.act("SEND_SAV_00_1",
            If(SAV, source.data.eq(0x00), NextState("SEND_SAV_00_2"))
        )
        fsm.act("SEND_SAV_00_2",
            If(SAV, source.data.eq(0x00), NextState("SEND_SAV_XY"))
        )
        fsm.act("SEND_SAV_XY",
            If(SAV, source.data.eq(xy), NextState("ACTIVE_VIDEO")),
            # row_cnt.eq(row_cnt+1)
            #  pixel_ready.eq(1)
        )
        # Active video: bytes 288–1727
        fsm.act("ACTIVE_VIDEO",
            If((DAL & VAP),
                # If(pix_phase == 0, source.data.eq(YCbCr[8:16])),
                # If(pix_phase == 1, source.data.eq(YCbCr[16:24])),
                # If(pix_phase == 2, source.data.eq(YCbCr[0:8])),
                # If(pix_phase == 3, source.data.eq(YCbCr[16:24]))
                If(pix_phase == 0, source.data.eq(sink.data[8:16])),
                If(pix_phase == 1, source.data.eq(sink.data[16:24])),
                If(pix_phase == 2, source.data.eq(sink.data[0:8])),
                If(pix_phase == 3, source.data.eq(sink.data[16:24]))
            ),
            If(~VAP & DAL, source.data.eq(Mux(h_count[1], 0x80, 0x10))),
            If(h_count == 1727, NextState("SEND_EAV_FF"))
        )
        # state phasae counter even DAL and VAP
        self.sync += [
            If(DAL & VAP,
                # Increment phase every clock cycle
                If(pix_phase == 3,
                    pix_phase.eq(0)
                ).Else(
                    pix_phase.eq(pix_phase + 1)
                ),
                # Row counter logic
                If(pix_phase > 1,
                    If(row_cnt == 719,
                        row_cnt.eq(0)
                    ).Else(
                        row_cnt.eq(row_cnt + 1)
                    )
                )
            ).Else(
                pix_phase.eq(0),
                row_cnt.eq(0)
            )
        ]
        self.comb += [
            If(DAL & VAP,
                If((pix_phase == 0) & (h_count == 288),
                    pixel_ready.eq(1)
                ).Elif(pix_phase > 1,
                    pixel_ready.eq(1)
                ).Else(
                    pixel_ready.eq(0)
                )
            ).Else(
                pixel_ready.eq(0)
            )
        ]

        self.comb += sink.ready.eq(pixel_ready)
        self.comb += sink.vdal.eq(DAL)
        self.comb += sink.vvap.eq(VAP)

        # ---------------------------------------------------------------------
        # Simple color bars / test pattern
        # ---------------------------------------------------------------------
        self.comb +=[
            # Horizontal pixel color test
            If((row_cnt < 179),  y.eq(82), cb.eq(90),cr.eq(240)),
            If((row_cnt >  179),  y.eq(120), cb.eq(54),cr.eq(34)),
            If((row_cnt > 359),  y.eq(82), cb.eq(90),cr.eq(240)),
            If((row_cnt >  539),  y.eq(120), cb.eq(54),cr.eq(34)),
           
            # vertical pixel color test
            # If((v_count >= 0)
            #     , y.eq(82), cb.eq(90),cr.eq(240)),
            # If((v_count >= 167)
            #     , y.eq(243), cb.eq(128),cr.eq(128)),
            # If((v_count >= 336)
            #     , y.eq(82), cb.eq(90),cr.eq(240)),
            # If((v_count >= 480)
            #     , y.eq(243), cb.eq(128),cr.eq(128)),          
            
            YCbCr.eq((y << 16)+(cb << 8)+ cr)
        ]