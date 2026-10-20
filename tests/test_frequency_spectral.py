"""Bit-true checks for the fixed frequency response and output conversion."""

from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from model.fixed_point import Format, constants


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl/frequency_optimized"
SOURCES = [RTL / name for name in (
    "frequency_csd_mul.sv", "frequency_complex_const.sv",
    "frequency_spectral16.sv", "frequency_output_scale.sv",
)]


def signed12(value):
    return value & 0xFFF


def pack12(values):
    return sum(signed12(value) << (12 * lane) for lane, value in enumerate(values))


def spectral_reference(i_values, q_values):
    _, (hr, hi), _ = constants(Format())
    out_i, out_q = [], []
    for ar, aq, coeff_r, coeff_i in zip(i_values, q_values, hr, hi):
        out_i.append((ar * int(coeff_r) - aq * int(coeff_i) + 128) >> 8)
        out_q.append((ar * int(coeff_i) + aq * int(coeff_r) + 128) >> 8)
    return out_i, out_q


def run_iverilog(bench_text, top):
    with tempfile.TemporaryDirectory() as directory:
        bench = Path(directory) / "bench.sv"
        executable = Path(directory) / "simulation.out"
        bench.write_text(bench_text)
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-s", top, "-o", str(executable),
             *map(str, SOURCES), str(bench)],
            cwd=ROOT, text=True, capture_output=True, timeout=20,
        )
        if compile_result.returncode:
            raise AssertionError(compile_result.stdout + compile_result.stderr)
        if not executable.exists():
            raise AssertionError("iverilog produced no output file: " + compile_result.stdout + compile_result.stderr)
        result = subprocess.run(["vvp", str(executable)], cwd=ROOT, text=True,
                                capture_output=True, timeout=20)
        if result.returncode and "Unable to open input file" in result.stderr:
            raise AssertionError(f"missing/invalid vvp output ({executable.stat().st_size} bytes): " + result.stderr)
        return result


class FrequencySpectralChecks(unittest.TestCase):
    def test_spectral_bins_pipeline_bubbles_and_reset(self):
        rng = random.Random(90416)
        vectors = [
            ([rng.randint(-128, 127) for _ in range(16)],
             [rng.randint(-128, 127) for _ in range(16)])
            for _ in range(9)
        ]
        # Include distinct consecutive samples, gaps, and reset while data is in flight.
        schedule = [
            (1, 0, vectors[0]), (1, 0, vectors[1]), (0, 0, None),
            (1, 0, vectors[2]), (0, 1, None), (0, 0, None),
            (1, 0, vectors[3]), (1, 0, vectors[4]), (1, 0, vectors[5]),
            (0, 0, None), (1, 0, vectors[6]), (0, 0, None),
            (1, 0, vectors[7]), (1, 0, vectors[8]), (0, 0, None),
        ]
        calls = []
        previous = None
        for valid, reset, sample in schedule:
            if reset:
                previous = None
            current_i, current_q = sample if sample else ([0] * 16, [0] * 16)
            expected_i, expected_q = spectral_reference(current_i, current_q)
            prev_i, prev_q = previous if previous else ([0] * 16, [0] * 16)
            calls.append(
                f"        step(1'b{reset}, 1'b{valid}, 192'h{pack12(current_i):048x}, "
                f"192'h{pack12(current_q):048x}, 192'h{pack12(expected_i):048x}, "
                f"192'h{pack12(expected_q):048x}, 192'h{pack12(prev_i):048x}, "
                f"192'h{pack12(prev_q):048x}, 1'b{int(previous is not None)});"
            )
            if reset:
                previous = None
            elif valid:
                previous = (expected_i, expected_q)
            else:
                previous = None

        bench = '''`timescale 1ns/1ps
module spectral_tb;
    reg clk = 0, rst = 1, in_valid = 0;
    reg [191:0] in_i = 0, in_q = 0;
    wire out_valid;
    wire [191:0] out_i, out_q;
    reg ext_valid = 0;
    reg [191:0] ext_i = 0, ext_q = 0;
    integer checks = 0;
    always #5 clk = ~clk;
    frequency_spectral16 dut(.clk(clk), .rst(rst), .in_valid(in_valid),
        .in_i(in_i), .in_q(in_q), .out_valid(out_valid), .out_i(out_i), .out_q(out_q));
    always @(posedge clk) begin
        if (rst) begin ext_valid <= 0; end
        else begin
            ext_valid <= out_valid;
            if (out_valid) begin ext_i <= out_i; ext_q <= out_q; end
        end
    end
    task step(input reg reset, input reg valid, input reg [191:0] ai, aq,
              input reg [191:0] ei, eq, prev_i, prev_q, input reg prev_valid);
    begin
        @(negedge clk); rst = reset; in_valid = valid; in_i = ai; in_q = aq;
        @(posedge clk); #1;
        if (out_valid !== (valid && !reset)) $fatal(1, "spectral valid mismatch");
        if (valid && !reset && (out_i !== ei || out_q !== eq))
            $fatal(1, "spectral output mismatch");
        if (ext_valid !== (prev_valid && !reset)) $fatal(1, "external valid mismatch");
        if (prev_valid && !reset && (ext_i !== prev_i || ext_q !== prev_q))
            $fatal(1, "external captured output mismatch");
        checks = checks + 1;
    end endtask
    initial begin
'''+"\n".join(calls)+'''
        $display("PASS spectral pipeline %0d", checks);
        $finish;
    end
endmodule
'''
        result = run_iverilog(bench, "spectral_tb")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS spectral pipeline", result.stdout)

    def test_output_scale_exhaustive_fitting_range(self):
        # For signed 9-bit output, ((x+2)>>2) fits exactly for x in [-1026, 1021].
        def pack9(values):
            return sum((value & 0x1FF) << (9 * lane) for lane, value in enumerate(values))

        cases = []
        for x in range(-1026, 1022):
            values_i = [x + (lane * 127 % 2048) for lane in range(8)]
            values_i = [-1026 + ((value + 1026) % 2048) for value in values_i]
            values_q = [1021 - ((x + lane * 251 + 1026) % 2048) for lane in range(8)]
            expected_i = [(value + 2) // 4 for value in values_i]
            expected_q = [(value + 2) // 4 for value in values_q]
            cases.append(
                f"        in_i = 96'h{pack12(values_i[:8]):024x}; "
                f"in_q = 96'h{pack12(values_q[:8]):024x}; #1; "
                f"if (out_i !== 72'h{pack9(expected_i):018x} || "
                f"out_q !== 72'h{pack9(expected_q):018x}) "
                f'$fatal(1, "scale mismatch case {x}");'
            )
        bench = '''`timescale 1ns/1ps
module scale_tb;
    reg [95:0] in_i = 0, in_q = 0;
    wire [71:0] out_i, out_q;
    frequency_output_scale dut(.in_i(in_i), .in_q(in_q), .out_i(out_i), .out_q(out_q));
    initial begin
'''+"\n".join(cases)+'''
        $display("PASS output scale exhaustive");
        $finish;
    end
endmodule
'''
        result = run_iverilog(bench, "scale_tb")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS output scale exhaustive", result.stdout)


if __name__ == "__main__":
    unittest.main()
