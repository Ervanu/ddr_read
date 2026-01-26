.PHONY: all b l f clean

all: info
b:
	@python -m soc.sp6_soc --build
l:
	@python -m soc.sp6_soc --load
f: 
	openFPGALoader -c dirtyJtag -f --fpga-part xc6slx25csg324 -o 0x00000 build/sp6_hw/gateware/sp6_hw.bin
# 	@python -m soc.sp6_soc --flash
clean:
	rm -rf build