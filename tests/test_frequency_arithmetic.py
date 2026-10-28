"""C04 arithmetic: exact constants, pipeline alignment, overflow assertions."""

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT / "rtl/frequency_optimized" / name for name in (
    "frequency_csd_mul.sv", "frequency_complex_const.sv",
)]


class FrequencyArithmeticChecks(unittest.TestCase):
    def simulate(self, bench, top, parameters=()):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "arithmetic.out"
            result = subprocess.run(
                ["iverilog", "-g2012", "-s", top, *parameters, "-o", str(executable),
                 *map(str, SOURCES), str(bench)],
                cwd=ROOT, text=True, capture_output=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return subprocess.run(["vvp", str(executable)], cwd=ROOT, text=True,
                                  capture_output=True, timeout=120)

    def test_exact_arithmetic_and_pipeline(self):
        result = self.simulate(
            ROOT / "tb/frequency_optimized/tb_frequency_arithmetic.sv",
            "tb_frequency_arithmetic",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS frequency arithmetic", result.stdout)

    def test_overflow_including_trivial_negation(self):
        with tempfile.TemporaryDirectory() as directory:
            bench = Path(directory) / "overflow.sv"
            bench.write_text('''`timescale 1ns/1ps
module overflow;
    parameter PIPE = 0;
    parameter AXIS = 0;
    reg clk = 0, rst = 1, valid = 0;
    wire ov;
    wire signed [11:0] ti, tq;
    always #5 clk = ~clk;
    frequency_complex_const #(.C_I(AXIS ? 356 : 0), .C_Q(AXIS ? 0 : -256),
                              .REGISTER_PRODUCTS(PIPE)) dut(
        .clk(clk), .rst(rst), .in_valid(valid), .a_i(-12'sd2048), .a_q(12'sd0),
        .out_valid(ov), .t_i(ti), .t_q(tq));
    initial begin
        repeat (2) @(negedge clk);
        rst = 0; valid = 1;
        repeat (5) @(negedge clk);
        $fatal(1, "Missing overflow assertion");
    end
endmodule
''')
            for pipeline in (0, 1):
                for axis in (0, 1):
                    with self.subTest(pipeline=pipeline, axis=axis):
                        result = self.simulate(bench, "overflow", (
                            f"-Poverflow.PIPE={pipeline}", f"-Poverflow.AXIS={axis}",
                        ))
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("frequency_complex_const: product overflows work", result.stdout)


if __name__ == "__main__":
    unittest.main()
