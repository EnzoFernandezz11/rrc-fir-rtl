"""A04: modelos de punto fijo, SQNR y ausencia de overflow."""

import unittest

import numpy as np

from model import fixed_point as fp
from model.fir_time import fir_time
from model.fixed_point import Format, evaluate, fir_frequency_fxp, fir_time_fxp, rshift_round, widths
from model.qpsk_rrc import PROJECT, qpsk, rrc_taps, upsample


class FixedPointChecks(unittest.TestCase):
    def test_chosen_format_meets_sqnr_in_both_branches(self):
        r = evaluate(Format())
        minimum = PROJECT["confirmed"]["minimum_sqnr_db"]
        self.assertGreaterEqual(r["tiempo"], minimum)
        self.assertGreaterEqual(r["frecuencia"], minimum)
        self.assertLessEqual(r["dif_lsb"], 2)  # tolerancia propuesta entre ramas

    def test_wide_format_converges_to_float_reference(self):
        # Valida la estructura de ambos modelos, independiente del formato elegido.
        f = Format(coef=24, out=24, work=24, twiddle=24, spectrum=24)
        h = rrc_taps()
        for n in (1, 7, 8, 9, 16, 75):  # trama vacía: test de A03 (#40)
            x = upsample(qpsk(40, 5))[:n]
            ref = fir_time(x, h)
            np.testing.assert_allclose(fir_time_fxp(x, f) / 2**24, ref, atol=1e-5)
            np.testing.assert_allclose(fir_frequency_fxp(x, f) / 2**24, ref, atol=1e-5)

    def test_output_width_matches_rtl_interface(self):
        out = PROJECT["decisions"]["rtl_interface"]["output"]
        self.assertEqual(widths(Format())["salida"], (out["width"], out["fraction_bits"]))

    def test_worst_case_windows_do_not_overflow_work(self):
        # Para cada nodo y etapa, la ventana de signos que maximiza |I| o |Q|.
        f = Format()
        _, H, W = fp.constants(f)
        trace = []
        fp._engine(np.eye(16), np.zeros((16, 16)), Format(f.coef, f.out, f.work, 0, 0),
                   (H[0] / 2**f.spectrum, H[1] / 2**f.spectrum), (W[0] / 2**f.twiddle, W[1] / 2**f.twiddle), None, trace)
        xi, xq = [], []
        for cr, ci in trace:  # cr[n, nodo]: coeficiente de la entrada n
            for node in range(16):
                xi += [np.sign(cr[:, node]), np.sign(ci[:, node])]  # máx. Re, máx. Im
                xq += [-np.sign(ci[:, node]), np.sign(cr[:, node])]
        xi, xq = np.array(xi, np.int64), np.array(xq, np.int64)
        xi, xq = np.where(xi == 0, xq, xi), np.where(xq == 0, xi, xq)  # mantener QPSK ±1±j
        bits = widths(f)["work"][0]
        trace = []
        fp._engine(xi << f.work, xq << f.work, f, H, W, bits, trace)  # levanta OverflowError
        peak = max(np.abs(np.r_[r.ravel(), i.ravel()]).max() for r, i in trace) / 2**f.work
        self.assertGreater(peak, 2 ** (bits - f.work - 2))  # la cota no sobra un bit entero

    def test_overflow_is_reported_not_wrapped(self):
        with self.assertRaises(OverflowError):
            fp.check("salida", np.array([256]), 9)

    def test_round_half_up_example(self):
        # 0,6893895… × (+1) y × (−1) con 7 bits: 88/128; recorte a 2 bits fraccionarios.
        h_q = fp.coefficients(Format())
        self.assertEqual(h_q[3], 88)
        self.assertEqual(list(rshift_round(np.array([88, -88, 80, -80, 79]), 5)), [3, -3, 3, -2, 2])

    def test_rejects_inputs_outside_two_bits(self):
        with self.assertRaises(ValueError):
            fir_time_fxp([2 + 0j])


if __name__ == "__main__":
    unittest.main()
