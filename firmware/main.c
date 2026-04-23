#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/common.h>
#include <irq.h>
#include <libbase/uart.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// void dump_memory(uint32_t start_addr, uint32_t count);

char buf[100];
void dump_memory(uint32_t start_addr, uint32_t count);

void uart_print(char *str) {
  // Loop until the pointer points to the null terminator '\0'
  while (*str != '\0') {
    uart_write(*str); // Send the current character
    str++;            // Move to the next character in the string
  }
}

int main(void) {
  irq_setmask(0);
  irq_setie(1);
  uart_init();
  // while (1) {
  //   uart_print("t\r\n");
  //   busy_wait(1000);
  // }
  uint32_t test_addr = 0x41000000; // Safe offset in DDR
  volatile uint32_t *ddr = (uint32_t *)test_addr;

  // Write some distinct patterns
  ddr[0] = 0x12345678;
  ddr[1] = 0xDEADBEEF;
  ddr[2] = 0xCAFEBABE;
  ddr[3] = 0x00112233;

  // // Dump it back to the terminal
  dump_memory(test_addr, 16);

  while (1)
    ;
}

void dump_memory(uint32_t start_addr, uint32_t count) {
  volatile uint32_t *ptr = (uint32_t *)start_addr;

  sprintf(buf, "\n--- Memory Dump [0x%08x] ---\n", start_addr);
  uart_print(buf);
  for (uint32_t i = 0; i < count; i++) {
    // Print address at the start of every 4 words (16 bytes)
    if (i % 4 == 0) {
      sprintf(buf, "\n0x%08x: ", (unsigned int)(start_addr + (i * 4)));
      uart_print(buf);
    }
    sprintf(buf, "%08x ", (unsigned int)ptr[i]);
    uart_print(buf);
  }
  uart_print("\n----------------------------\n");
}