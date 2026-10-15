"""Ejercita el lector A05 real del testbench con archivos temporales."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.validate_project import ROOT


class FrequencyVectorChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.directory = Path(directory.name)
        cls.executable = cls.directory / "frequency.out"
        targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
        target = next(t for t in targets if t["name"] == "frequency_serial")
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", target["testbench_top"], "-o", str(cls.executable),
             *target["sources"], target["testbench"]],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
        if compiled.returncode:
            raise RuntimeError(compiled.stdout)

    def simulate(self, path):
        return subprocess.run(
            ["vvp", str(self.executable), f"+a05_file={path}"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )

    def test_official_frames_with_and_without_pauses(self):
        result = self.simulate(ROOT / "vectors/bordes.txt")
        self.assertEqual(result.returncode, 0, result.stdout)
        for pauses in (0, 1):
            self.assertIn(f"202 muestras, 19 tramas, pausas={pauses}", result.stdout)

    def test_frequency_column_is_exact(self):
        path = self.directory / "columnas.txt"
        # En cero, yt deliberadamente distinto no debe afectar la comparación de yf.
        path.write_text("0 1 0 0 1 -1 0 0\n")
        result = self.simulate(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        path.write_text("0 1 0 0 0 0 1 0\n")
        result = self.simulate(path)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("esperado (1,0), obtenido (0,0)", result.stdout)
        self.assertIn(str(path), result.stdout)

    def test_overflow_is_checked_at_each_output_handshake(self):
        bench = self.directory / "overflow.sv"
        bench.write_text('''`timescale 1ns/1ps
module overflow;
    reg clk=0, rst=1, in_valid=0, in_last=0, out_ready=1;
    always #5 clk=~clk;
    wire in_ready, out_valid, out_last;
    wire signed [8:0] out_i, out_q;
    integer index, imaginary, sent;
    fir_frequency_serial dut(.clk(clk), .rst(rst), .in_i(2'sd0), .in_q(2'sd0),
        .in_valid(in_valid), .in_last(in_last), .in_ready(in_ready),
        .out_i(out_i), .out_q(out_q), .out_valid(out_valid), .out_last(out_last),
        .out_ready(out_ready));
    initial begin
        if (!$value$plusargs("index=%d", index) || !$value$plusargs("imaginary=%d", imaginary))
            $fatal(1, "Missing test arguments");
        repeat (2) @(negedge clk);
        rst=0; in_valid=1; sent=0;
        while (sent<8) begin
            @(posedge clk);
            if (in_ready) sent=sent+1;
            @(negedge clk);
            in_last=(sent==7);
        end
        in_valid=0; in_last=0;
        wait(out_valid);
        while (dut.engine_result_index != index) @(negedge clk);
        // Corrupt one stored result only after computation, then hold it stalled.
        out_ready=0;
        if (imaginary) dut.u_engine.work_q[8+index]=-2048;
        else dut.u_engine.work_i[8+index]=2047;
        repeat (3) @(negedge clk);
        $display("HELD overflow without handshake");
        out_ready=1;
        @(posedge clk); #1;
        $fatal(1, "Overflow was not detected");
    end
    initial begin #20000; $fatal(1, "Test timeout"); end
endmodule
''')
        executable = self.directory / "overflow.out"
        targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
        target = next(t for t in targets if t["name"] == "frequency_serial")
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "overflow", "-o", str(executable),
             *target["sources"], str(bench)],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
        self.assertEqual(compiled.returncode, 0, compiled.stdout)
        for index in range(8):
            for imaginary in (0, 1):
                with self.subTest(index=index, imaginary=imaginary):
                    result = subprocess.run(
                        ["vvp", str(executable), f"+index={index}", f"+imaginary={imaginary}"],
                        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10,
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn("HELD overflow without handshake", result.stdout)
                    self.assertIn("frequency_block_engine: result overflows output", result.stdout)

    def test_invalid_files_fail_with_location(self):
        cases = {
            "vacio": ("", "archivo vacio", 0),
            "incompleto": ("0 1 0 0 0 0 0\n", "ocho columnas", 0),
            "fila_partida": ("0 1 0 0\n0 0 0 0\n", "ocho columnas", 0),
            "extra": ("0 1 0 0 0 0 0 0 extra\n", "ocho columnas", 0),
            "indice": ("1 1 0 0 0 0 0 0\n", "indice discontinuo", 0),
            "entrada": ("0 1 -2 0 0 0 0 0\n", "fuera de rango", 0),
            "salida": ("0 1 0 0 0 0 256 0\n", "fuera de rango", 0),
            "last": ("0 2 0 0 0 0 0 0\n", "fuera de rango", 0),
            "desconocido": ("0 1 x 0 0 0 0 0\n", "valor desconocido", 0),
            "alta_impedancia": ("0 1 0 0 0 0 0 z\n", "valor desconocido", 0),
            "sin_last": ("0 0 0 0 0 0 0 0\n", "trama sin last", 0),
            "trama_larga": ("".join(f"{n} 0 0 0 0 0 0 0\n" for n in range(2049)),
                            "trama supera 2048", 2048),
        }
        for name, (content, message, index) in cases.items():
            with self.subTest(name=name):
                path = self.directory / f"{name}.txt"
                path.write_text(content)
                result = self.simulate(path)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(message, result.stdout)
                self.assertIn(f"A05 {path} indice {index}", result.stdout)
        path = self.directory / "ausente.txt"
        result = self.simulate(path)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"A05 {path} indice 0: no se pudo abrir", result.stdout)


if __name__ == "__main__":
    unittest.main()
