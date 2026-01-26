# uart_tx.py
from migen import *
from migen.genlib.fsm import FSM, NextState, NextValue

class UARTTXCHAR(Module):
    def __init__(self, uart_sink, data_bytes):
        """
        uart_sink : UARTPHY.sink endpoint
        data_bytes: Python list of integers (0–255)
        """

        depth = len(data_bytes)
        index = Signal(max=depth)

        # Convert Python list → hardware array
        rom = Array(Constant(b, 8) for b in data_bytes)
        self.submodules.fsm = fsm = FSM(reset_state="SEND")
        fsm.act("SEND",
            uart_sink.valid.eq(1),
            uart_sink.data.eq(rom[index]),
            If(uart_sink.ready,
                If(index == depth - 1,
                    NextState("DONE")
                ).Else(
                    NextValue(index, index + 1)
                )
            )
        )
        fsm.act("DONE",
            uart_sink.valid.eq(0)
        )

class UARTTX32(Module):
    def __init__(self, uart_sink, words):
        """
        uart_sink : UARTPHY.sink
        words     : Python list of 32-bit integers (len = 64)
        """

        assert len(words) == 64

        word_count = 64
        byte_count = 4

        word_idx = Signal(max=word_count)
        byte_idx = Signal(2)  # 0..3

        rom = Array(Constant(w, 32) for w in words)

        self.submodules.fsm = fsm = FSM(reset_state="SEND")

        current_word = Signal(32)
        self.comb += current_word.eq(rom[word_idx])

        # Select byte (LSB-first)
        byte = Signal(8)
        self.comb += byte.eq(current_word >> (byte_idx * 8))

        fsm.act("SEND",
            uart_sink.valid.eq(1),
            uart_sink.data.eq(byte),

            If(uart_sink.ready,
                If(byte_idx == byte_count - 1,
                    NextValue(byte_idx, 0),
                    If(word_idx == word_count - 1,
                        NextState("DONE")
                    ).Else(
                        NextValue(word_idx, word_idx + 1)
                    )
                ).Else(
                    NextValue(byte_idx, byte_idx + 1)
                )
            )
        )

        fsm.act("DONE",
            uart_sink.valid.eq(0)
        )

        
# class UARTTX32Single(Module):
#     def __init__(self, uart_sink, word32):
#         # 6 bytes → need 3 bits
#         byte_idx = Signal(3)
#         byte_reg = Signal(8)
#         counter = Signal(32)

#         # FSM
#         self.submodules.fsm = fsm = FSM(reset_state="SEND")

#         # SEND state
#         fsm.act("SEND",
#             uart_sink.valid.eq(1),
#             uart_sink.data.eq(byte_reg),

#             If(uart_sink.ready,
#                 # update byte
#                 If(byte_idx == 0,
#                     NextValue(byte_reg, word32[0:8])
#                 ).Elif(byte_idx == 1,
#                     NextValue(byte_reg, word32[8:16])
#                 ).Elif(byte_idx == 2,
#                     NextValue(byte_reg, word32[16:24])
#                 ).Elif(byte_idx == 3,
#                     NextValue(byte_reg, word32[24:32])
#                 ).Elif(byte_idx == 4,
#                     NextValue(byte_reg, 0x0A)
#                 ).Elif(byte_idx == 5,
#                     NextValue(byte_reg, 0x0D)
#                 ),

#                 # update index
#                 If(byte_idx == 5,
#                     NextValue(byte_idx, 0),
#                     NextState("DONE")
#                 ).Else(
#                     NextValue(byte_idx, byte_idx + 1)
#                 )
#             )
#         )

#         # DONE state: wait counter cycles before sending again
#         fsm.act("DONE",
#             uart_sink.valid.eq(0),
#             If(counter == 10_000_000-1,
#                 NextValue(counter, 0),
#                 NextState("SEND")
#             ).Else(
#                 NextValue(counter, counter + 1)
#             )
#         )

class UARTTX32Single(Module):
    def __init__(self, uart_sink, word32):
        # Ensure word32 is a Migen-slicable object (Signal or Constant)
        word32 = wrap(word32)

        byte_idx = Signal(3)
        byte_reg = Signal(8)
        counter = Signal(32)

        self.is_done = Signal()

        # 1. DATA SELECTION (Combinatorial)
        # We drive the sink data based on the current index immediately
        self.comb += [
            Case(byte_idx, {
                0: uart_sink.data.eq(word32[0:8]),
                1: uart_sink.data.eq(word32[8:16]),
                2: uart_sink.data.eq(word32[16:24]),
                3: uart_sink.data.eq(word32[24:32]),
                4: uart_sink.data.eq(0x0A), # \n
                5: uart_sink.data.eq(0x0D), # \r
            })
        ]

        # 2. FSM LOGIC
        self.submodules.fsm = fsm = FSM(reset_state="SEND")

        fsm.act("SEND",
            uart_sink.valid.eq(1),
            self.is_done.eq(0),
            # Wait for UART to accept the current byte
            If(uart_sink.ready,
                If(byte_idx == 5,
                    NextValue(byte_idx, 0),
                    NextState("DONE")
                ).Else(
                    NextValue(byte_idx, byte_idx + 1)
                )
            )
        )

        fsm.act("DONE",
            uart_sink.valid.eq(0),
            self.is_done.eq(1),
            # Delay before next transmission (approx 10M cycles)
            If(counter == 10_000_000 - 1,
                NextValue(counter, 0),
                NextState("SEND")
            ).Else(
                NextValue(counter, counter + 1)
            )
        )
