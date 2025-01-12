# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch
import json
import os
import unittest

from cubigma.utils import (
    get_prefix_order_number_quartet,
    index_to_quartet,
    pad_chunk_with_rand_pad_symbols,
    quartet_to_index,
    read_config,
    remove_duplicate_letters,
    sanitize,
    split_to_human_readable_symbols,
    strengthen_key,
    user_perceived_length,
)
from cubigma.utils import _cascade_gap, _find_symbol, _split_key_into_parts  # noqa

LENGTH_OF_QUARTET = 4

# Testing Private Functions


class TestCascadeGap(unittest.TestCase):
    def setUp(self):
        self.playfair_cuboid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]

    def test_cascade_gap_forward_front(self):
        # Test cascading forward
        expected_cuboid = [
            [["A", "B"], ["C", "D", "E"], ["F", "G", "H"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]
        letter_i = self.playfair_cuboid[0][2].pop(2)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 0, 2, direction="to-front")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_cascade_gap_forward_middle(self):
        expected_cuboid = [
            [["A", "B"], ["C", "D", "E"], ["F", "G", "H"]],
            [["I", "J", "K"], ["L", "M", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]
        letter_n = self.playfair_cuboid[1][1].pop(1)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 1, 1, direction="to-front")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_cascade_gap_forward_back(self):
        expected_cuboid = [
            [["A", "B"], ["C", "D", "E"], ["F", "G", "H"]],
            [["I", "J", "K"], ["L", "M", "N"], ["O", "P", "Q"]],
            [["R", "S", "T"], ["U", "V", "W"], ["X", "Y", "Z"]],
        ]
        letter_zero = self.playfair_cuboid[2][2].pop(2)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 2, 2, direction="to-front")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_cascade_gap_reverse_back(self):
        expected_cuboid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["T", "U", "V"], ["W", "X", "Y"], ["Z", "0"]],
        ]
        letter_s = self.playfair_cuboid[2][0].pop(0)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 2, 0, direction="to-back")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_cascade_gap_reverse_middle(self):
        expected_cuboid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "O", "P"], ["Q", "R", "S"]],
            [["T", "U", "V"], ["W", "X", "Y"], ["Z", "0"]],
        ]
        letter_n = self.playfair_cuboid[1][1].pop(1)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 1, 1, direction="to-back")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_cascade_gap_reverse_front(self):
        expected_cuboid = [
            [["B", "C", "D"], ["E", "F", "G"], ["H", "I", "J"]],
            [["K", "L", "M"], ["N", "O", "P"], ["Q", "R", "S"]],
            [["T", "U", "V"], ["W", "X", "Y"], ["Z", "0"]],
        ]
        letter_a = self.playfair_cuboid[0][0].pop(0)
        resultant_cuboid = _cascade_gap(self.playfair_cuboid, 0, 0, direction="to-back")
        self.assertEqual(expected_cuboid, resultant_cuboid)

    def test_invalid_direction(self):
        # Test invalid direction
        with self.assertRaises(ValueError):
            _cascade_gap(self.playfair_cuboid, 0, 0, direction="to-the-left")


class TestFindSymbol(unittest.TestCase):
    def setUp(self):
        # Example 3x3x3 playfair cuboid
        self.playfair_cuboid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]

    def test_find_symbol_valid(self):
        # Test cases for valid symbols
        self.assertEqual(_find_symbol("A", self.playfair_cuboid), (0, 0, 0))
        self.assertEqual(_find_symbol("E", self.playfair_cuboid), (0, 1, 1))
        self.assertEqual(_find_symbol("R", self.playfair_cuboid), (1, 2, 2))
        self.assertEqual(_find_symbol("Z", self.playfair_cuboid), (2, 2, 1))

    def test_find_symbol_not_found(self):
        # Test for a symbol that is not in the cuboid
        with self.assertRaises(ValueError) as context:
            _find_symbol("1", self.playfair_cuboid)
        self.assertEqual(str(context.exception), "Symbol '1' not found in playfair_cuboid.")

    def test_find_symbol_edge_cases(self):
        # Test for edge cases like last element
        self.assertEqual(_find_symbol("0", self.playfair_cuboid), (2, 2, 2))
        self.assertEqual(_find_symbol("Z", self.playfair_cuboid), (2, 2, 1))
        self.assertEqual(_find_symbol("X", self.playfair_cuboid), (2, 1, 2))
        self.assertEqual(_find_symbol("R", self.playfair_cuboid), (1, 2, 2))


class TestSplitKeyIntoParts(unittest.TestCase):
    def test_even_division(self):
        """Test when the sanitized key phrase length is evenly divisible by the number of rotors."""
        result = _split_key_into_parts("ABCDEFGHI", 3)
        self.assertEqual(result, ["ABC", "DEF", "GHI"])

    def test_uneven_division(self):
        """Test when the sanitized key phrase length is not evenly divisible by the number of rotors."""
        result = _split_key_into_parts("ABCDEFGHIJK", 3)
        self.assertEqual(result, ["ABC", "DEF", "GHIJK"])

    def test_single_rotor(self):
        """Test when there is only one rotor."""
        result = _split_key_into_parts("ABCDEFGHI", 1)
        self.assertEqual(result, ["ABCDEFGHI"])

    def test_empty_string(self):
        """Test when the sanitized key phrase is an empty string."""
        with self.assertRaises(ValueError):
            _split_key_into_parts("", 3)

    def test_more_rotors_than_characters(self):
        """Test when the number of rotors exceeds the length of the sanitized key phrase."""
        with self.assertRaises(ValueError):
            _split_key_into_parts("AB", 5)

    def test_zero_rotors(self):
        """Test when the number of rotors is zero (should raise an error)."""
        with self.assertRaises(ValueError):
            _split_key_into_parts("ABCD", 0)

    def test_negative_rotors(self):
        """Test when the number of rotors is negative (should raise an error)."""
        with self.assertRaises(ValueError):
            _split_key_into_parts("ABCD", -3)


# Testing Public Functions


class TestGetPrefixOrderNumberQuartet(unittest.TestCase):
    def test_valid_order_number(self):
        """Test that a valid single-digit order number returns a quartet of symbols including the order number."""
        order_number = 5
        result = get_prefix_order_number_quartet(order_number)

        # Check that the result has exactly 4 characters
        self.assertEqual(len(result), 4, "Resulting string does not have 4 characters")

        # Check that the result contains the order number
        self.assertIn(str(order_number), result, f"Order number {order_number} is not in the result")

        # Check that all expected padding symbols are included
        pad_symbols = ["\x07", "\x16", "\x06", str(order_number)]
        for symbol in pad_symbols:
            self.assertIn(symbol, result, f"Symbol {symbol} is missing from the result")

    def test_invalid_order_number(self):
        """Test that an invalid order number raises an assertion error."""
        with self.assertRaises(AssertionError):
            get_prefix_order_number_quartet(10)  # Not a single-digit number

        with self.assertRaises(AssertionError):
            get_prefix_order_number_quartet(-1)  # Negative number

        with self.assertRaises(AssertionError):
            get_prefix_order_number_quartet(123)  # Multiple digits

    def test_randomness(self):
        """Test that the function produces different outputs for the same input due to shuffling."""
        order_number = 3
        results = {get_prefix_order_number_quartet(order_number) for _ in range(100)}

        # Verify that we have multiple unique outputs, indicating randomness
        self.assertGreater(len(results), 1, "Function does not produce randomized outputs")


class TestIndexToQuartet(unittest.TestCase):
    def setUp(self):
        self.symbols = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            " ",
            ".",
            "🏖️",
            "🏵️",
            "🌮",
            "🖐️",
        ]

    def test_valid_numbers(self):
        self.assertEqual("dung", index_to_quartet(3802574, self.symbols))
        self.assertEqual("Dung", index_to_quartet(11977806, self.symbols))
        self.assertEqual("🏖️🏵️🌮🖐️", index_to_quartet(20428763, self.symbols))
        self.assertEqual("1234", index_to_quartet(16599263, self.symbols))
        self.assertEqual(index_to_quartet(0, self.symbols), "qqqq")
        self.assertEqual(index_to_quartet(1, self.symbols), "qqqw")
        self.assertEqual(index_to_quartet(2, self.symbols), "qqqe")
        self.assertEqual(index_to_quartet(3, self.symbols), "qqqr")
        self.assertEqual(index_to_quartet(4, self.symbols), "qqqt")
        self.assertEqual(index_to_quartet(8, self.symbols), "qqqo")
        self.assertEqual(index_to_quartet(16, self.symbols), "qqqj")
        self.assertEqual(index_to_quartet(32, self.symbols), "qqqU")
        self.assertEqual(index_to_quartet(85, self.symbols), "qqwk")

    def test_edge_cases(self):
        # Test edge cases like the maximum index and rollover
        max_index = (len(self.symbols) ** 4) - 1
        self.assertEqual(index_to_quartet(max_index, self.symbols), "🖐️🖐️🖐️🖐️")

    def test_invalid_symbols(self):
        # Test cases with invalid or empty symbols list
        with self.assertRaises(ValueError):
            index_to_quartet(0, [])

        with self.assertRaises(ValueError):
            index_to_quartet(0, ["q"])  # Not enough symbols to form a quartet

    def test_symbols_with_special_characters(self):
        # Test symbols with special characters
        special_symbols = ["@", "#", "$", "%"]
        self.assertEqual(index_to_quartet(42, special_symbols), "@$$$")


class TestPadChunkWithRandPadSymbols(unittest.TestCase):
    @patch("cubigma.utils.random")
    def test_pad_chunk_with_empty_input(self, mock_randint):
        with self.assertRaises(ValueError) as context:
            pad_chunk_with_rand_pad_symbols("")
        self.assertIn("Chunk cannot be empty", str(context.exception))

    @patch("random.randint")
    def test_pad_chunk_with_one_length_input(self, mock_randint):
        mock_randint.side_effect = [0, 1, 2]
        result = pad_chunk_with_rand_pad_symbols("A")
        self.assertEqual(result, "A\x07\x16\x06")

    @patch("random.randint")
    def test_pad_chunk_with_two_length_input(self, mock_randint):
        mock_randint.side_effect = [2, 1]
        result = pad_chunk_with_rand_pad_symbols("AB")
        self.assertEqual(result, "AB\x06\x16")

    @patch("random.randint")
    def test_pad_chunk_with_three_length_input(self, mock_randint):
        mock_randint.side_effect = [0]
        result = pad_chunk_with_rand_pad_symbols("ABC")
        self.assertEqual(result, "ABC\x07")

    @patch("random.randint")
    def test_pad_chunk_with_full_length_input(self, mock_randint):
        result = pad_chunk_with_rand_pad_symbols("ABCD")
        self.assertEqual(result, "ABCD")


class TestQuartetToIndex(unittest.TestCase):
    def setUp(self):
        self.symbols = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            " ",
            ".",
            "🏖️",
            "🏵️",
            "🌮",
            "🖐️",
        ]

    def test_valid_quartet(self):
        """Test normal usage with valid inputs."""
        self.assertEqual(3802574, quartet_to_index("dung", self.symbols))
        self.assertEqual(11977806, quartet_to_index("Dung", self.symbols))
        self.assertEqual(20428763, quartet_to_index("🏖️🏵️🌮🖐️", self.symbols))
        self.assertEqual(16599263, quartet_to_index("1234", self.symbols))
        self.assertEqual(0, quartet_to_index("qqqq", self.symbols))
        self.assertEqual(1, quartet_to_index("qqqw", self.symbols))
        self.assertEqual(2, quartet_to_index("qqqe", self.symbols))
        self.assertEqual(3, quartet_to_index("qqqr", self.symbols))
        self.assertEqual(4, quartet_to_index("qqqt", self.symbols))
        self.assertEqual(8, quartet_to_index("qqqo", self.symbols))
        self.assertEqual(16, quartet_to_index("qqqj", self.symbols))
        self.assertEqual(32, quartet_to_index("qqqU", self.symbols))
        self.assertEqual(85, quartet_to_index("qqwk", self.symbols))

    def test_edge_case(self):
        """Test edge cases with minimum and maximum symbol values."""
        min_quartet = self.symbols[0] * LENGTH_OF_QUARTET
        max_quartet = self.symbols[-1] * LENGTH_OF_QUARTET
        expected_max_index = (len(self.symbols) ** 4) - 1
        self.assertEqual(quartet_to_index(min_quartet, self.symbols), 0)
        self.assertEqual(quartet_to_index(max_quartet, self.symbols), expected_max_index)

    def test_invalid_quartet_length(self):
        """Test that a ValueError is raised if the quartet does not have 4 elements."""
        with self.assertRaises(ValueError):
            quartet_to_index("123", self.symbols)
        with self.assertRaises(ValueError):
            quartet_to_index("12345", self.symbols)

    def test_invalid_symbol_value(self):
        """Test that an exception is raised for invalid symbol values."""
        with self.assertRaises(ValueError):
            quartet_to_index("123🇬🇵", self.symbols)  # Symbol is not present in cuboid.txt


class TestReadConfig(unittest.TestCase):
    def setUp(self):
        # Sample valid configuration data
        self.valid_config = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}

    @patch("cubigma.utils.Path")
    @patch("cubigma.utils.json.load")
    def test_read_valid_config(self, mock_load, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = True
        mock_load.return_value = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}

        # Act
        config = read_config("mock_config.json")

        # Assert
        self.assertEqual(config, self.valid_config)
        mock_path.return_value.open.assert_called_once_with("r", encoding="utf-8")
        mock_load.assert_called_once()

    @patch("cubigma.utils.Path")
    def test_missing_config_file(self, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = False

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            read_config("missing_config.json")

    @patch("cubigma.utils.Path")
    def test_invalid_json_format(self, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = True
        mock_path.return_value.open.return_value.__enter__.return_value.read.return_value = "{'Not valid json'"

        # Act & Assert
        with self.assertRaises(json.JSONDecodeError):
            read_config("invalid_config.json")
        mock_path.return_value.open.assert_called_once_with("r", encoding="utf-8")
        mock_path.return_value.open.return_value.__enter__.return_value.read.assert_called_once()


class TestRemoveDuplicateLetters(unittest.TestCase):

    def test_empty_string(self):
        """Test that an empty string returns an empty string."""
        self.assertEqual(remove_duplicate_letters(""), "")

    def test_single_character(self):
        """Test that a single character string returns itself."""
        self.assertEqual(remove_duplicate_letters("a"), "a")

    def test_all_unique_characters(self):
        """Test that a string with all unique characters returns the same string."""
        self.assertEqual(remove_duplicate_letters("abc"), "abc")

    def test_repeated_characters(self):
        """Test that repeated characters are removed, keeping only the first occurrence."""
        self.assertEqual(remove_duplicate_letters("aabbcc"), "abc")

    def test_mixed_characters(self):
        """Test that mixed characters with repetitions return the correct result."""
        self.assertEqual(remove_duplicate_letters("abacada"), "abcd")

    def test_case_sensitivity(self):
        """Test that the function is case-sensitive."""
        self.assertEqual(remove_duplicate_letters("AaAaBbBb"), "AaBb")

    def test_numbers_and_special_characters(self):
        """Test that numbers and special characters are handled correctly."""
        self.assertEqual(remove_duplicate_letters("123123!@!@"), "123!@")

    def test_long_string(self):
        """Test with a long string to ensure performance and correctness."""
        self.assertEqual(remove_duplicate_letters("a" * 1000 + "b" * 1000), "ab")


class TestSanitizeFunction(unittest.TestCase):
    def test_escape_sequences(self):
        """Test if escape sequences are properly converted."""
        # Act & Assert
        self.assertEqual(sanitize("\\n"), "\n", "Failed to convert newline escape sequence.")
        self.assertEqual(sanitize("\\t"), "\t", "Failed to convert tab escape sequence.")
        self.assertEqual(sanitize("\\\\"), "\\", "Failed to convert backslash escape sequence.")

    def test_mixed_escape_sequences(self):
        """Test if mixed escape sequences are handled correctly."""
        input_str = "\\nSome\\tText\\\\Here"
        expected_output = "\nSome\tText\\Here"

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle mixed escape sequences.")

    def test_plain_string(self):
        """Test if a plain string without leading backslash is returned unchanged except for newline removal."""
        input_str = "This is a test string.\nWith newline."
        expected_output = "This is a test string.With newline."

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle plain string correctly.")

    def test_string_with_no_modifications(self):
        """Test if a string without newlines or leading backslash is returned unchanged."""
        input_str = "This is a test string."
        expected_output = "This is a test string."

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle string with no modifications.")

    def test_empty_string(self):
        """Test if an empty string is handled correctly."""
        input_str = ""
        expected_output = ""

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle empty string.")

    def test_leading_backslash_with_plain_text(self):
        """Test if leading backslash with plain text is handled correctly."""
        input_str = "\\Hello"
        expected_output = "\\Hello"

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle leading backslash with plain text.")

    def test_only_backslashes(self):
        """Test if a string with only backslashes is handled correctly."""
        input_str = "\\\\\\"
        expected_output = "\\\\"

        # Act & Assert
        self.assertEqual(sanitize(input_str), expected_output, "Failed to handle string with only backslashes.")


class TestSplitToHumanReadableSymbols(unittest.TestCase):

    def test_valid_input(self):
        """Test valid input with exactly 4 human-discernible symbols."""
        self.assertEqual(split_to_human_readable_symbols("áb̂c̃d̄"), ["á", "b̂", "c̃", "d̄"])

        self.assertEqual(split_to_human_readable_symbols("😊é́👍🏽🎉"), ["😊", "é́", "👍🏽", "🎉"])

    def test_mixed_grapheme_clusters(self):
        """Test input with mixed grapheme clusters (combining marks and emojis)."""
        self.assertEqual(split_to_human_readable_symbols("👩‍❤️‍💋‍👨á😊👍🏽"), ["👩‍❤️‍💋‍👨", "á", "😊", "👍🏽"])

    def test_invalid_input_length(self):
        """Test input with invalid user-perceived lengths."""
        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("abc")  # 3 graphemes

        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("abcde")  # 5 graphemes

        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("áb̂c̃d̄e")  # 5 graphemes

    def test_empty_string(self):
        """Test an empty string input, which should raise an error."""
        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("")

    def test_non_string_input(self):
        """Test non-string input, which should raise a TypeError."""
        with self.assertRaises(TypeError):
            split_to_human_readable_symbols(None)  # noqa

        with self.assertRaises(TypeError):
            split_to_human_readable_symbols(1234)  # noqa

    def test_valid_combining_characters(self):
        """Test valid input with combining characters to form graphemes."""
        self.assertEqual(split_to_human_readable_symbols("éôũī"), ["é", "ô", "ũ", "ī"])


class TestStrengthenKey(unittest.TestCase):

    def test_key_generation_with_salt(self):
        """Test that strengthen_key generates a key when a salt is provided."""
        key_phrase = "test-key"
        salt = os.urandom(16)
        key, returned_salt = strengthen_key(key_phrase, salt=salt)

        self.assertIsInstance(key, bytes)
        self.assertIsInstance(returned_salt, bytes)
        self.assertEqual(len(returned_salt), 16)
        self.assertEqual(returned_salt, salt)

    def test_key_generation_without_salt(self):
        """Test that strengthen_key generates a key and random salt when no salt is provided."""
        key_phrase = "test-key"
        key, salt = strengthen_key(key_phrase)

        self.assertIsInstance(key, bytes)
        self.assertIsInstance(salt, bytes)
        self.assertEqual(len(salt), 16)

    def test_key_derivation_is_consistent(self):
        """Test that the same key phrase and salt produce the same key."""
        key_phrase = "test-key"
        salt = os.urandom(16)
        key1, _ = strengthen_key(key_phrase, salt=salt)
        key2, _ = strengthen_key(key_phrase, salt=salt)

        self.assertEqual(key1, key2)

    def test_different_salts_produce_different_keys(self):
        """Test that different salts produce different keys."""
        key_phrase = "test-key"
        salt1 = os.urandom(16)
        salt2 = os.urandom(16)
        key1, _ = strengthen_key(key_phrase, salt=salt1)
        key2, _ = strengthen_key(key_phrase, salt=salt2)

        self.assertNotEqual(key1, key2)

    def test_key_length_parameter(self):
        """Test that the derived key length matches the specified key_length."""
        key_phrase = "test-key"
        key_length = 64
        key, _ = strengthen_key(key_phrase, key_length=key_length)

        self.assertEqual(len(key), key_length)

    def test_invalid_key_phrase_type(self):
        """Test that passing a non-string key phrase raises a TypeError."""
        with self.assertRaises(AttributeError):
            strengthen_key(12345)  # noqa

    def test_invalid_salt_type(self):
        """Test that passing a non-bytes salt raises a TypeError."""
        with self.assertRaises(TypeError):
            strengthen_key("test-key", salt="invalid-salt")  # noqa

    def test_invalid_iterations_value(self):
        """Test that invalid iteration counts raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", iterations=-1)

    def test_invalid_key_length(self):
        """Test that invalid key lengths raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", key_length=0)


class TestUserPerceivedLength(unittest.TestCase):
    def test_basic_text(self):
        self.assertEqual(user_perceived_length("hello"), 5)
        self.assertEqual(user_perceived_length(""), 0)
        self.assertEqual(user_perceived_length("a"), 1)

    def test_emojis(self):
        self.assertEqual(user_perceived_length("🙂"), 1)
        self.assertEqual(user_perceived_length("🙂🙂"), 2)

    def test_surrogate_pairs(self):
        self.assertEqual(user_perceived_length("👨‍👩‍👧‍👦"), 1)  # Family emoji
        self.assertEqual(user_perceived_length("👩‍❤️‍💋‍👨"), 1)  # Couple kissing emoji

    def test_combining_characters(self):
        self.assertEqual(user_perceived_length("á"), 1)  # "á" as 'a' + combining acute accent
        self.assertEqual(user_perceived_length("éé"), 2)  # Two "é"
        self.assertEqual(user_perceived_length("é́"), 1)  # One "e" with two combining marks

    def test_mixed_content(self):
        self.assertEqual(user_perceived_length("hello🙂"), 6)
        self.assertEqual(user_perceived_length("🙂á"), 2)
        self.assertEqual(user_perceived_length("🙂👩‍❤️‍💋‍👨"), 2)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
