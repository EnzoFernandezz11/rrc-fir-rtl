"""Run the shared A05 reader contract against the optimized public interface."""
import unittest
from tests import test_frequency_vectors as shared


class OptimizedVectorChecks(unittest.TestCase):
    target_name = "frequency_optimized"
    setUpClass = classmethod(shared.FrequencyVectorChecks.setUpClass.__func__)
    simulate = shared.FrequencyVectorChecks.simulate
    test_official_frames_with_and_without_pauses = shared.FrequencyVectorChecks.test_official_frames_with_and_without_pauses
    test_frequency_column_is_exact = shared.FrequencyVectorChecks.test_frequency_column_is_exact
    test_invalid_files_fail_with_location = shared.FrequencyVectorChecks.test_invalid_files_fail_with_location


if __name__ == "__main__":
    unittest.main()
