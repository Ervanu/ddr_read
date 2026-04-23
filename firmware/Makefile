BUILD_DIR?=../build/sp6_hw

include $(BUILD_DIR)/software/include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

OBJECTS   = crt0.o main.o
CFLAGS 	 += -Iinc
ifdef WITH_CXX
	OBJECTS += hellocpp.o
	CFLAGS += -DWITH_CXX
endif


a: firmware.bin


%.bin: %.elf
	$(OBJCOPY) -O binary -j .text -j .rodata -j .data -j .bss $< $@
ifneq ($(OS),Windows_NT)
	chmod -x $@
endif

vpath %.a $(PACKAGES:%=../%)

firmware.elf: $(OBJECTS)
	    $(CC) $(LDFLAGS) $(CFLAGS) -T linker.ld -N -o $@ \
		$(OBJECTS) \
		$(PACKAGES:%=-L$(BUILD_DIR)/software/%) \
		-Wl,--whole-archive \
		-Wl,--gc-sections \
		-Wl,-Map,$@.map \
		-Wl,--whole-archive -lbase \
		-Wl,--no-whole-archive \
		$(LIBS:lib%=-l%)

ifneq ($(OS),Windows_NT)
	chmod -x $@
endif

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

donut.o: CFLAGS   += -w

VPATH = $(BIOS_DIRECTORY):$(BIOS_DIRECTORY)/cmds:$(CPU_DIRECTORY):src


%.o: %.cpp
	$(compilexx)

%.o: %.c
	$(compile)

%.o: %.S
	$(assemble)

c:
	$(RM) $(OBJECTS) firmware.elf firmware.bin *.map .*~ *~ *.d *.o *.fbi
fb: 
	python wrap_firmware.py  
f:
	openFPGALoader -c dirtyJtag -f --fpga-part xc6slx25csg324 -o 0xd0000 firmware.fbi
all: 
	make c a fb f

.PHONY: all c f a fb
