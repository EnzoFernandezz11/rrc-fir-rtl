"""C04 transforms against all eight FFT/IFFT checkpoints of the existing model."""

from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np

from model.fixed_point import Format, _engine, constants

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT / "rtl/frequency_optimized" / name for name in (
    "frequency_csd_mul.sv", "frequency_complex_const.sv",
    "frequency_butterfly.sv", "frequency_fft16.sv",
)]


class FrequencyTransformChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.directory = Path(directory.name)
        cls.executable = cls.directory / "transform.out"
        result = subprocess.run(
            ["iverilog", "-g2012", "-s", "tb_frequency_transform", "-o", str(cls.executable),
             *map(str, SOURCES), str(ROOT / "tb/frequency_optimized/tb_frequency_transform.sv")],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        rng = np.random.default_rng(42)
        xr, xq = (rng.integers(-1, 2, (256, 16), dtype=np.int64)*32 for _ in range(2))
        # Every input position, I/Q separately, plus the full coherent extremes.
        xr[:64], xq[:64] = 0, 0
        for n in range(16):
            xr[n, n] = 32
            xq[16+n, n] = -32
            xr[32+n, n], xq[32+n, n] = 32, -32
        for n, (real, imag) in enumerate(((32, 32), (32, -32), (-32, 32), (-32, -32))):
            xr[64+n], xq[64+n] = real, imag
        _, h, w = constants(Format())
        trace = []
        _engine(xr, xq, Format(), h, w, 12, trace)
        cls.vectors = cls.directory / "vectors.txt"
        with cls.vectors.open("w") as out:
            out.write(f"{len(xr)}\n")
            for n in range(len(xr)):
                vectors = [(xr, xq), trace[4], *trace[:4], *trace[5:]]
                for real, imag in vectors:
                    out.write(" ".join(f"{r} {i}" for r, i in zip(real[n], imag[n])) + "\n")

    def test_stage_values_latency_bubbles_and_reset(self):
        for mode in (0, 1, 2):
            with self.subTest(mode=mode):
                result = subprocess.run(
                    ["vvp", str(self.executable), f"+vectors={self.vectors}", f"+mode={mode}"],
                    cwd=ROOT, text=True, capture_output=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("PASS transforms", result.stdout)

    def test_butterfly_overflow(self):
        bench = self.directory / "butterfly_overflow.sv"
        bench.write_text('''`timescale 1ns/1ps
module butterfly_overflow;
    parameter PIPE = 0;
    reg clk=0, rst=1, valid=0;
    wire v;
    wire signed [11:0] si,sq,di,dq;
    always #5 clk=~clk;
    frequency_butterfly #(.REGISTER_PRODUCTS(PIPE)) dut(
        .clk(clk), .rst(rst), .in_valid(valid),
        .a_i(12'sd2047), .a_q(12'sd0), .b_i(12'sd1), .b_q(12'sd0),
        .out_valid(v), .sum_i(si), .sum_q(sq), .diff_i(di), .diff_q(dq));
    initial begin
        repeat(2) @(negedge clk);
        rst=0; valid=1;
        repeat(5) @(negedge clk);
        $fatal(1,"Missing butterfly overflow");
    end
endmodule
''')
        for pipeline in (0, 1):
            with self.subTest(pipeline=pipeline):
                executable = self.directory / f"butterfly{pipeline}.out"
                result = subprocess.run(
                    ["iverilog", "-g2012", "-s", "butterfly_overflow",
                     f"-Pbutterfly_overflow.PIPE={pipeline}", "-o", str(executable),
                     *map(str, SOURCES), str(bench)],
                    text=True, capture_output=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                result = subprocess.run(["vvp", str(executable)], text=True, capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("frequency_butterfly: butterfly overflows work", result.stdout)


if __name__ == "__main__":
    unittest.main()
