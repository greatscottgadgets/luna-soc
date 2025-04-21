#
# This file is part of LUNA.
#
# Copyright (c) 2025 S. Holzapfel <me@sebholzapfel.com>
# Copyright (c) 2023-2025 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Utilities for simulating luna-soc designs with Verilator."""

import glob
import os
import shutil
import subprocess

from amaranth              import *
from amaranth.back         import verilog
from amaranth.build        import *
from amaranth.lib          import wiring, data
from amaranth.lib.wiring   import In, Out

from amaranth_soc          import gpio

def is_hw(platform):
    # assumption: anything that inherits from Platform is a
    # real hardware platform. Anything else isn't.
    # is there a more idiomatic way of doing this?
    return isinstance(platform, Platform)

class VerilatorPlatform():

    class FakeDomainGenerator(Elaboratable):

        def __init__(self, *, clock_frequencies=None, clock_signal_name=None):
            pass

        def elaborate(self, platform):
            m = Module()

            m.domains.sync   = ClockDomain()

            return m

    clock_domain_generator = FakeDomainGenerator

    def __init__(self):
        self.name = "verilator_platform"
        self.files = {}

    def has_required_tools(self):
        return True

    def add_file(self, file_name, contents):
        if not file_name.endswith('.svh'):
            self.files[file_name] = contents

    def ports(self, fragment):
        return {
            "clk_sync":       (ClockSignal("sync"),                          None),
            "rst_sync":       (ResetSignal("sync"),                          None),
            "uart0_w_data":   (fragment.soc.uart0._tx_data.f.data.w_data,    None),
            "uart0_w_stb":    (fragment.soc.uart0._tx_data.f.data.w_stb,     None),
        }

    def request(self, name, ix):
        match name:
            case "uart":
                return wiring.Signature({
                    "rx": In(wiring.Signature({"i": Out(unsigned(1))})),
                    "tx": Out(wiring.Signature({"o": Out(unsigned(1))}))
                    }).create()
            case "led":
                return wiring.Signature({"o": Out(unsigned(1))}).create()

    def build(self, fragment, do_program, build_dir):

        harness = "tb_cpp/sim_soc.cpp"

        os.makedirs(build_dir, exist_ok=True)
        verilog_dst = os.path.join(build_dir, "luna_soc.v")
        with open(verilog_dst, "w") as f:
            f.write(verilog.convert(
                fragment,
                platform=self,
                ports=self.ports(fragment)
                ))

        # Write all additional files added with platform.add_file()
        # to build/ directory, so verilator build can find them.
        for file in self.files:
            with open(os.path.join("build", file), "w") as f:
                f.write(self.files[file])

        tracing = True
        tracing_flags = ["--trace-fst", "--trace-structs"] if tracing else []

        verilator_dst = os.path.join(build_dir, "obj_dir")
        shutil.rmtree(verilator_dst, ignore_errors=True)

        # Copy shared testbench headers somewhere Verilator's build
        # process can see them.
        os.makedirs(verilator_dst)
        testbench_utils = glob.glob("./tb_cpp/*.h")
        for header in testbench_utils:
            shutil.copy(header, verilator_dst)

        print(f"verilate '{verilog_dst}' into C++ binary...")
        subprocess.check_call(["verilator",
                               "-Wno-COMBDLY",
                               "-Wno-CASEINCOMPLETE",
                               "-Wno-CASEOVERLAP",
                               "-Wno-WIDTHEXPAND",
                               "-Wno-WIDTHTRUNC",
                               "-Wno-TIMESCALEMOD",
                               "-Wno-PINMISSING",
                               "-Wno-ASCRANGE",
                               "-Wno-UNSIGNED",
                               "-cc"] + tracing_flags + [
                               "--exe",
                               "--Mdir", f"{verilator_dst}",
                               "-Ibuild",
                               "--build",
                               "-j", "0",
                               "-CFLAGS", f"-DSYNC_CLK_HZ={fragment.clock_frequency_hz}",
                               harness,
                               f"{verilog_dst}",
                              ] + [
                                   f for f in self.files
                                   if f.endswith(".svh") or f.endswith(".sv") or f.endswith(".v")
                              ],
                              env=os.environ)
