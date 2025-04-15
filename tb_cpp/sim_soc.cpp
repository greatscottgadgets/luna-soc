// A (quite dirty) simulation harness that simulates the luna_soc core
// and uses it to generate some full FST traces for examination.

#include <cmath>

#if VM_TRACE_FST == 1
#include <verilated_fst_c.h>
#endif

#include "Vluna_soc.h"
#include "verilated.h"

#include <fstream>

int main(int argc, char** argv) {
    VerilatedContext* contextp = new VerilatedContext;
    contextp->commandArgs(argc, argv);
    Vluna_soc* top = new Vluna_soc{contextp};

#if VM_TRACE_FST == 1
    Verilated::traceEverOn(true);
    VerilatedFstC* tfp = new VerilatedFstC;
    top->trace(tfp, 99);  // Trace 99 levels of hierarchy (or see below)
    tfp->open("simx.fst");
#endif

    uint64_t sim_time =  5000e9;

    uint64_t ns_in_s = 1e9;
    uint64_t ns_in_sync_cycle   = ns_in_s /  SYNC_CLK_HZ;
    printf("sync domain is: %i KHz (%i ns/cycle)\n",  SYNC_CLK_HZ/1000,  ns_in_sync_cycle);

    contextp->timeInc(1);
    top->rst_sync = 1;
    top->eval();

#if VM_TRACE_FST == 1
    tfp->dump(contextp->time());
#endif

    contextp->timeInc(1);
    top->rst_sync = 0;
    top->eval();

#if VM_TRACE_FST == 1
    tfp->dump(contextp->time());
#endif

    while (contextp->time() < sim_time && !contextp->gotFinish()) {

        uint64_t timestamp_ns = contextp->time() / 1000;

        // Sync clock domain (PSRAM read/write simulation, UART printouts)
        if (timestamp_ns % (ns_in_sync_cycle/2) == 0) {
            top->clk_sync = !top->clk_sync;
            top->eval();
            if (top->clk_sync) {
                if (top->uart0_w_stb) {
                    putchar(top->uart0_w_data);
                }
            }
        }

        contextp->timeInc(1000);
        top->eval();
#if VM_TRACE_FST == 1
        tfp->dump(contextp->time());
#endif
    }
#if VM_TRACE_FST == 1
    tfp->close();
#endif
    return 0;
}
