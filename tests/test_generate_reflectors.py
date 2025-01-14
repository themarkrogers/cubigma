# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

import unittest

from cubigma.generate_reflectors import generate_reflector


class TestGenerateReflector(unittest.TestCase):
    def setUp(self):
        """
        Set up reusable inputs for the tests.
        """
        self.key_phrase = "test_key"
        self.num_symbols_even = 10
        self.num_symbols_odd = 11

    def test_reflector_deterministic(self):
        """
        Test that the output of the reflector is deterministic given the same key phrase and number of symbols.
        """
        result1 = generate_reflector(self.key_phrase, self.num_symbols_even)
        result2 = generate_reflector(self.key_phrase, self.num_symbols_even)
        self.assertEqual(result1, result2, "Reflector output should be deterministic.")

    def test_even_number_of_symbols(self):
        """
        Test that the reflector pairs all symbols correctly for an even number of symbols.
        """
        result = generate_reflector(self.key_phrase, self.num_symbols_even)
        # Check that all symbols are paired and pairs are symmetric
        for key, value in result.items():
            self.assertEqual(result[value], key, "Reflector pairs should be symmetric.")
        self.assertEqual(len(result), self.num_symbols_even, "Reflector should contain all symbols.")

    def test_odd_number_of_symbols(self):
        """
        Test that the reflector handles an odd number of symbols correctly, leaving one symbol mapped to itself.
        """
        result = generate_reflector(self.key_phrase, self.num_symbols_odd)
        unpaired = [key for key, value in result.items() if key == value]
        self.assertEqual(len(unpaired), 1, "There should be exactly one unpaired symbol.")

        # Check that all other symbols are properly paired
        for key, value in result.items():
            if key != value:
                self.assertEqual(result[value], key, "Reflector pairs should be symmetric.")
        self.assertEqual(len(result), self.num_symbols_odd, "Reflector should contain all symbols.")

    def test_empty_reflector(self):
        """
        Test that the function returns an empty reflector when the number of symbols is 0.
        """
        result = generate_reflector(self.key_phrase, 0)
        self.assertEqual(result, {}, "Reflector should be empty for 0 symbols.")

    def test_single_symbol_reflector(self):
        """
        Test that the function returns a reflector with one symbol mapping to itself for one symbol.
        """
        result = generate_reflector(self.key_phrase, 1)
        self.assertEqual(result, {0: 0}, "Reflector should map the single symbol to itself.")


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
