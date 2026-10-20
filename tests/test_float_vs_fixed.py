"""I02: flotante contra fijo en cada conjunto de datos."""

import math
import unittest

from model.float_vs_fixed import compare, datasets
from model.qpsk_rrc import PROJECT


class FloatVsFixedChecks(unittest.TestCase):
    def test_every_dataset_meets_sqnr_and_error_bound(self):
        minimum = PROJECT["confirmed"]["minimum_sqnr_db"]
        for name, frames in datasets().items():
            for branch, r in compare(frames).items():
                with self.subTest(caso=name, rama=branch):
                    self.assertLessEqual(r["max_lsb"], 2.5)
                    if name == "ceros":
                        self.assertEqual(r["max_lsb"], 0)
                        self.assertTrue(math.isnan(r["sqnr_db"]))
                    else:
                        self.assertGreaterEqual(r["sqnr_db"], minimum)


if __name__ == "__main__":
    unittest.main()
