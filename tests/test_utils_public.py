# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, MagicMock
import json
import unittest

from cubigma.utils import (
    LENGTH_OF_TRIO,
    generate_cube_from_symbols,
    generate_plugboard,
    generate_reflector,
    generate_rotors,
    get_symbol_for_coordinates,
    get_encrypted_coordinates,
    pad_chunk,
    parse_arguments,
    prep_string_for_encrypting,
    read_config,
    rotate_slice_of_cube,
    sanitize,
    split_to_human_readable_symbols,
    _user_perceived_length,
)


class TestGenerateCubeFromSymbols(unittest.TestCase):
    def setUp(self):
        # Common test setup for symbols
        self.symbols = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]

    @patch("cubigma.utils._user_perceived_length")
    def test_generate_cube_valid_input(self, mock_length):
        """Test cube generation with valid input."""
        # Arrange
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 3
        expected_output = [[["a", "b", "c"], ["d", "e", "f"]], [["g", "h", "i"], ["j", "k", "l"]]]
        mock_length.side_effect = [LENGTH_OF_TRIO, LENGTH_OF_TRIO, LENGTH_OF_TRIO, LENGTH_OF_TRIO]

        # Act
        result = generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)

        # Assert
        self.assertEqual(result, expected_output)
        assert mock_length.call_count == 4
        mock_length.assert_any_call("abc")
        mock_length.assert_any_call("def")
        mock_length.assert_any_call("ghi")
        mock_length.assert_any_call("jkl")

    @patch("cubigma.utils._user_perceived_length")
    def test_generate_cube_edge_case_single_block(self, mock_length):
        """Test cube generation with only one block."""
        # Arrange
        num_blocks = 1
        lines_per_block = 2
        symbols_per_line = 3
        expected_output = [[["a", "b", "c"], ["d", "e", "f"]]]
        mock_length.side_effect = [LENGTH_OF_TRIO, LENGTH_OF_TRIO]

        # Act
        result = generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)

        # Assert
        self.assertEqual(result, expected_output)
        assert mock_length.call_count == 2
        mock_length.assert_any_call("abc")
        mock_length.assert_any_call("def")

    @patch("cubigma.utils._user_perceived_length")
    def test_generate_cube_invalid_symbols_length(self, mock_length):
        """Test failure when symbols length does not match required input dimensions."""
        # Arrange
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 4
        mock_length.side_effect = [LENGTH_OF_TRIO, LENGTH_OF_TRIO]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)
        self.assertEqual(str(context.exception), "Something has failed")
        mock_length.assert_called_once_with("abcd")

    @patch("cubigma.utils._user_perceived_length")
    def test_generate_cube_escape_characters(self, mock_length):
        """Test cube generation with escape characters in symbols."""
        # Arrange
        symbols_with_escape = ["a", "\\", "\n", "b", "\t", "c", "d", "e", "f", "g", "h", "i"]
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 3
        expected_output = [[["a", "\\", "\n"], ["b", "\t", "c"]], [["d", "e", "f"], ["g", "h", "i"]]]
        mock_length.side_effect = [LENGTH_OF_TRIO, LENGTH_OF_TRIO, LENGTH_OF_TRIO, LENGTH_OF_TRIO]

        # Act
        result = generate_cube_from_symbols(symbols_with_escape, num_blocks, lines_per_block, symbols_per_line)

        # Assert
        self.assertEqual(expected_output, result)
        assert mock_length.call_count == 4
        mock_length.assert_any_call("a\\\n")
        mock_length.assert_any_call("b\tc")
        mock_length.assert_any_call("def")
        mock_length.assert_any_call("ghi")

    @patch("cubigma.utils._user_perceived_length")
    def test_generate_cube_empty_symbols(self, mock_length):
        """Test cube generation with empty symbols list."""
        # Arrange
        symbols = []
        num_blocks = 0
        lines_per_block = 0
        symbols_per_line = 0
        expected_output = []

        # Act
        result = generate_cube_from_symbols(symbols, num_blocks, lines_per_block, symbols_per_line)

        # Assert
        self.assertEqual(result, expected_output)
        mock_length.assert_not_called()


class TestGeneratePlugboard(unittest.TestCase):

    @patch("cubigma.utils.split_to_human_readable_symbols")
    def test_valid_plugboard_values(self, mock_split):
        # Arrange
        plugboard_values = ["AB", "CD", "EF"]
        expected_output = {"A": "B", "B": "A", "C": "D", "D": "C", "E": "F", "F": "E"}
        mock_split.side_effect = [["A", "B"], ["C", "D"], ["E", "F"]]

        # Act
        result = generate_plugboard(plugboard_values)

        # Assert
        self.assertEqual(result, expected_output)
        assert mock_split.call_count == 3
        mock_split.assert_any_call("AB", expected_number_of_graphemes=None)
        mock_split.assert_any_call("CD", expected_number_of_graphemes=None)
        mock_split.assert_any_call("EF", expected_number_of_graphemes=None)

    @patch("cubigma.utils.split_to_human_readable_symbols")
    def test_empty_plugboard_values(self, mock_split):
        # Arrange
        plugboard_values = []
        expected_output = {}

        # Act
        result = generate_plugboard(plugboard_values)

        # Assert
        self.assertEqual(result, expected_output)
        mock_split.assert_not_called()

    @patch("cubigma.utils.split_to_human_readable_symbols")
    def test_invalid_plugboard_value_length(self, mock_split):
        # Arrange
        plugboard_values = ["A", "BCD", "EF"]
        mock_split.side_effect = [["A"], ["B", "C", "D"], ["E", "F"]]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            generate_plugboard(plugboard_values)
        self.assertIn("Plugboard values are expected to all be pairs of symbols.", str(context.exception))
        mock_split.assert_called_once_with("A", expected_number_of_graphemes=None)

    @patch("cubigma.utils.split_to_human_readable_symbols")
    def test_duplicate_symbols(self, mock_split):
        # Arrange
        plugboard_values = ["AB", "AC"]
        mock_split.side_effect = [["A", "B"], ["A", "C"]]

        # Act & Assert
        with self.assertRaises(ValueError):
            generate_plugboard(plugboard_values)
        assert mock_split.call_count == 2
        mock_split.assert_any_call("AB", expected_number_of_graphemes=None)
        mock_split.assert_any_call("AC", expected_number_of_graphemes=None)

    @patch("cubigma.utils.split_to_human_readable_symbols")
    def test_non_string_symbols(self, mock_split):
        # Arrange
        plugboard_values = [123, "AB"]
        mock_split.side_effect = TypeError()

        # Act & Assert
        with self.assertRaises(TypeError):
            generate_plugboard(plugboard_values)
        mock_split.assert_called_once_with(123, expected_number_of_graphemes=None)


class TestGenerateReflector(unittest.TestCase):

    def setUp(self):
        self.symbols = ["A", "B", "C", "D", "E", "F"]

        # Mocking DeterministicRandomCore
        self.random_core = MagicMock()
        self.random_core.shuffle = lambda x: x[::-1]  # Reverse list for deterministic behavior

    def test_reflector_bidirectional_mapping(self):
        """Test if the reflector creates bidirectional mappings."""
        reflector = generate_reflector(self.symbols, self.random_core)

        for symbol, mapped_symbol in reflector.items():
            self.assertEqual(reflector[mapped_symbol], symbol, "Mapping is not bidirectional")

    def test_all_symbols_mapped(self):
        """Test if all symbols are included in the reflector."""
        reflector = generate_reflector(self.symbols, self.random_core)

        self.assertSetEqual(set(reflector.keys()), set(self.symbols), "Not all symbols are mapped")
        self.assertSetEqual(set(reflector.values()), set(self.symbols), "Not all symbols are in values")

    def test_odd_number_of_symbols(self):
        """Test if function handles odd number of symbols by pairing the last symbol with itself."""
        odd_symbols = ["A", "B", "C", "D", "E"]
        self.random_core.shuffle = lambda x: x[::]  # Preserve list order
        reflector = generate_reflector(odd_symbols, self.random_core)

        for symbol in odd_symbols:
            self.assertIn(symbol, reflector, f"Symbol {symbol} is missing in reflector")
            self.assertIn(reflector[symbol], odd_symbols, f"Symbol {reflector[symbol]} is not valid")

            # Verify last symbol pairs with itself if list is odd
            if symbol == "E":
                self.assertNotEqual(reflector[symbol], symbol, "Odd symbol should not be paired with itself")

    def test_empty_symbols_list(self):
        """Test if function handles an empty symbols list."""
        reflector = generate_reflector([], self.random_core)
        self.assertEqual(reflector, {}, "Reflector for empty symbols list is not empty")

    def test_single_symbol(self):
        """Test if function handles a single symbol by mapping it to itself."""
        single_symbol = ["A"]
        reflector = generate_reflector(single_symbol, self.random_core)
        self.assertEqual(reflector, {"A": "A"}, "Single symbol is not paired with itself")


class TestGenerateRotors(unittest.TestCase):
    def setUp(self):
        self.valid_key = "testkey"
        self.valid_cube = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "1"]],
        ]
        self.num_rotors_to_make = 5
        self.rotors_to_use = [0, 3, 4]

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_generate_rotors_valid_input(self, mock_shuffle):
        """Test function with valid inputs."""
        mock_shuffle.side_effect = lambda key, cube, unique_val: cube  # Mock shuffle function

        result = generate_rotors(
            self.valid_key,
            self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
            orig_key_length=42,
        )

        self.assertEqual(len(result), len(self.rotors_to_use))
        for rotor in result:
            self.assertEqual(rotor, self.valid_cube)

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_missing_key_phrase(self, mock_shuffle):
        """Test function raises error on missing or invalid key phrase."""
        with self.assertRaises(ValueError):
            generate_rotors(
                "",
                self.valid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=self.rotors_to_use,
                orig_key_length=42,
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_invalid_num_rotors_to_make(self, mock_shuffle):
        """Test function raises error on invalid num_rotors_to_make."""
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                self.valid_cube,
                num_rotors_to_make=-1,
                rotors_to_use=self.rotors_to_use,
                orig_key_length=42,
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_invalid_rotors_to_use_values(self, mock_shuffle):
        """Test function raises error on invalid rotors_to_use."""
        invalid_rotors = [0, 5, 1, 1]  # Duplicate and out-of-range values
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                self.valid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=invalid_rotors,
                orig_key_length=42,
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_invalid_rotors_to_use_not_list(self, mock_shuffle):
        """Test function raises error on invalid rotors_to_use."""
        invalid_rotors = "[0, 5, 1, 1]"
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                self.valid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=invalid_rotors,
                orig_key_length=42,
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_invalid_cube(self, mock_shuffle):
        """Test function raises error on invalid rotors_to_use."""
        invalid_cube = [["AB", "CD"], ["EF", "GH"]]
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                invalid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=self.rotors_to_use,
                orig_key_length=42,
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_invalid_key_length(self, mock_shuffle):
        """Test function raises error on invalid rotors_to_use."""
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                self.valid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=self.rotors_to_use,
                orig_key_length="42",
            )

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_rotors_correct_count(self, mock_shuffle):
        """Test function generates the correct number of rotors."""
        mock_shuffle.side_effect = lambda key, cube, unique_val: cube

        result = generate_rotors(
            self.valid_key,
            self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
            orig_key_length=42,
        )

        self.assertEqual(len(result), len(self.rotors_to_use))

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_deterministic_output(self, mock_shuffle):
        """Test function produces deterministic output for the same inputs."""
        mock_shuffle.side_effect = lambda key, cube, unique_val: cube

        result1 = generate_rotors(
            self.valid_key,
            self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
            orig_key_length=42,
        )

        result2 = generate_rotors(
            self.valid_key,
            self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
            orig_key_length=42,
        )

        self.assertEqual(result1, result2)


class TestGetCharsForCoordinates(unittest.TestCase):

    def test_get_chars_for_valid_coordinates(self):
        # Arrange
        test_rotor = [[["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]]
        coordinate = (0, 2, 1)
        expected_result = "8"

        # Act
        result = get_symbol_for_coordinates(coordinate, test_rotor)

        # Assert
        self.assertEqual(expected_result, result)

    def test_get_chars_for_invalid_coordinates(self):
        # Arrange
        test_rotor = [[["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]]
        coordinate = (1, 0, 2)

        # Act & Assert
        with self.assertRaises(IndexError):
            get_symbol_for_coordinates(coordinate, test_rotor)


class TestGetOppositeCorners(unittest.TestCase):
    def setUp(self):
        self.num_blocks = 4
        self.lines_per_block = 4
        self.symbols_per_line = 4
        self.key_phrase = "testkey"
        self.num_trios_encoded = 1

    @patch("cubigma.utils._cyclically_permute_coordinates")
    @patch("cubigma.utils._invert_coordinates")
    @patch("cubigma.utils._transpose_coordinates")
    @patch("cubigma.utils.shuffle_for_input")
    def test_valid_input(self, mock_shuffle, mock_transpose, mock_invert, mock_cycle):
        # Arrange
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 1)
        point_3 = (0, 1, 0)
        points_order_1 = [point_1, point_2, point_3]
        points_order_2 = [point_1, point_3, point_2]
        points_order_3 = [point_3, point_2, point_1]
        points_order_4 = [point_2, point_3, point_1]
        mock_cycle.return_value = points_order_2
        mock_invert.return_value = points_order_3
        mock_transpose.return_value = points_order_4
        mock_shuffle.return_value = [mock_cycle, mock_invert, mock_transpose]
        expected_key = f"{self.key_phrase}|{self.num_trios_encoded}"

        # Act
        result = get_encrypted_coordinates(
            point_1,
            point_2,
            point_3,
            self.num_blocks,
            self.key_phrase,
            self.num_trios_encoded,
            True,
        )

        # Assert
        mock_shuffle.assert_called_once_with(expected_key, [mock_cycle, mock_invert, mock_transpose])
        mock_cycle.assert_called_once_with(points_order_1, self.num_blocks, True, expected_key)
        mock_invert.assert_called_once_with(points_order_2, self.num_blocks, True, expected_key)
        mock_transpose.assert_called_once_with(points_order_3, self.num_blocks, True, expected_key)
        self.assertEqual(result, points_order_4)

    @patch("cubigma.utils._cyclically_permute_coordinates")
    @patch("cubigma.utils._invert_coordinates")
    @patch("cubigma.utils._transpose_coordinates")
    @patch("cubigma.utils.shuffle_for_input")
    def test_non_unique_points(self, mock_shuffle, mock_transpose, mock_invert, mock_cycle):
        # Arrange
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 0)  # Duplicate
        point_3 = (0, 1, 0)
        points_order_1 = [point_1, point_2, point_3]
        points_order_2 = [point_1, point_3, point_2]
        points_order_3 = [point_3, point_2, point_1]
        points_order_4 = [point_2, point_3, point_1]
        mock_cycle.return_value = points_order_2
        mock_invert.return_value = points_order_3
        mock_transpose.return_value = points_order_4
        mock_shuffle.return_value = [mock_cycle, mock_invert, mock_transpose]
        expected_key = f"{self.key_phrase}|{self.num_trios_encoded}"

        # Act
        result = get_encrypted_coordinates(
            point_1,
            point_2,
            point_3,
            self.num_blocks,
            self.key_phrase,
            self.num_trios_encoded,
            True,
        )

        # Assert
        mock_shuffle.assert_called_once_with(expected_key, [mock_cycle, mock_invert, mock_transpose])
        mock_cycle.assert_called_once_with(points_order_1, self.num_blocks, True, expected_key)
        mock_invert.assert_called_once_with(points_order_2, self.num_blocks, True, expected_key)
        mock_transpose.assert_called_once_with(points_order_3, self.num_blocks, True, expected_key)
        self.assertEqual(result, points_order_4)

    @patch("cubigma.utils._cyclically_permute_coordinates")
    @patch("cubigma.utils._invert_coordinates")
    @patch("cubigma.utils._transpose_coordinates")
    @patch("cubigma.utils.shuffle_for_input")
    def test_key_phrase_affects_result(self, mock_shuffle, mock_transpose, mock_invert, mock_cycle):
        # Arrange
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 1)
        point_3 = (0, 1, 0)
        points_order_1 = [point_1, point_2, point_3]
        points_order_2 = [point_1, point_3, point_2]
        points_order_3 = [point_2, point_1, point_3]
        points_order_4 = [point_2, point_3, point_1]
        points_order_5 = [point_3, point_2, point_1]
        points_order_6 = [point_3, point_1, point_2]
        points_order_7 = [point_1, point_3, point_2]
        shuffle_order_1 = [mock_cycle, mock_invert, mock_transpose]
        shuffle_order_2 = [mock_transpose, mock_cycle, mock_invert]
        mock_cycle.side_effect = [points_order_2, points_order_3]
        mock_invert.side_effect = [points_order_4, points_order_5]
        mock_transpose.side_effect = [points_order_6, points_order_7]
        mock_shuffle.side_effect = [shuffle_order_1, shuffle_order_2]
        test_key_1 = "key1"
        test_key_2 = "key2"
        expected_key_1 = f"{test_key_1}|{self.num_trios_encoded}"
        expected_key_2 = f"{test_key_2}|{self.num_trios_encoded}"

        # Act
        result_1 = get_encrypted_coordinates(
            point_1,
            point_2,
            point_3,
            self.num_blocks,
            test_key_1,
            self.num_trios_encoded,
            True,
)
        result_2 = get_encrypted_coordinates(
            point_1,
            point_2,
            point_3,
            self.num_blocks,
            test_key_2,
            self.num_trios_encoded,
            True,
        )

        # Assert
        assert mock_shuffle.call_count == 2
        mock_shuffle.assert_any_call(expected_key_1, shuffle_order_1)
        mock_shuffle.assert_any_call(expected_key_2, shuffle_order_1)
        assert mock_cycle.call_count == 2
        mock_cycle.assert_any_call(points_order_1, self.num_blocks, True, expected_key_1)
        mock_cycle.assert_any_call(points_order_7, self.num_blocks, True, expected_key_2)
        assert mock_invert.call_count == 2
        mock_invert.assert_any_call(points_order_2, self.num_blocks, True, expected_key_1)
        mock_invert.assert_any_call(points_order_3, self.num_blocks, True, expected_key_2)
        assert mock_transpose.call_count == 2
        mock_transpose.assert_any_call(points_order_4, self.num_blocks, True, expected_key_1)
        mock_transpose.assert_any_call(points_order_1, self.num_blocks, True, expected_key_2)
        self.assertEqual(result_1, points_order_6)
        self.assertEqual(result_2, points_order_5)
        self.assertNotEqual(result_1, result_2)


class TestPadChunk(unittest.TestCase):
    def setUp(self):
        self.chunk_order_number = 2
        self.rotor = [[["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]]]

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    @patch("cubigma.utils._get_random_noise_chunk")
    @patch("cubigma.utils._get_prefix_order_number_trio")
    def test_pad_chunk_even_length(
        self, mock_get_prefix_order_number_trio, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols
    ):
        # Arrange
        mock_get_prefix_order_number_trio.return_value = "ORD"
        mock_get_random_noise_chunk.return_value = "XXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "BLA"
        expected_result = "ORDBLAXXXXXX"
        padded_chunk_length = 9

        # Act
        result = pad_chunk(test_chunk, padded_chunk_length, self.chunk_order_number, self.rotor)

        # Assert
        self.assertTrue(result.startswith("ORD"))
        self.assertEqual(result, expected_result)
        self.assertEqual(len(result[LENGTH_OF_TRIO:]), padded_chunk_length)
        mock_get_prefix_order_number_trio.assert_called_once_with(self.chunk_order_number)
        mock_get_random_noise_chunk.assert_called()
        mock_pad_chunk_with_rand_pad_symbols.assert_not_called()

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    @patch("cubigma.utils._get_random_noise_chunk")
    @patch("cubigma.utils._get_prefix_order_number_trio")
    def test_pad_chunk_short_length(
        self, mock_get_prefix_order_number_trio, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols
    ):
        # Arrange
        mock_get_prefix_order_number_trio.return_value = "ORD"
        mock_get_random_noise_chunk.return_value = "XXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "FU"
        expected_result = "ORDFUPXXXXXX"
        padded_chunk_length = 9

        # Act
        result = pad_chunk(test_chunk, padded_chunk_length, self.chunk_order_number, self.rotor)

        # Assert
        self.assertTrue(result.startswith("ORD"))
        self.assertEqual(result, expected_result)
        self.assertEqual(len(result[LENGTH_OF_TRIO:]), padded_chunk_length)
        mock_get_prefix_order_number_trio.assert_called_once_with(self.chunk_order_number)
        mock_get_random_noise_chunk.assert_called()
        mock_pad_chunk_with_rand_pad_symbols.assert_called_once_with(test_chunk)


class TestParseArguments(unittest.TestCase):
    @patch("builtins.input", side_effect=["test_key", "test_message"])
    @patch("cubigma.utils._read_and_validate_config")  # Replace 'cubigma.utils' with the actual module name
    def test_parse_arguments_with_inputs(self, mock_read_and_validate_config, mock_input):
        """Test parse_arguments function with interactive inputs."""
        # Mock the return value of _read_and_validate_config
        mock_read_and_validate_config.return_value = (
            5,  # cube_length
            3,  # num_rotors_to_make
            [1, 2, 3],  # rotors_to_use
            "encrypt",  # mode
            True,  # should_use_steganography
            ["AB"],  # plugboard values
        )

        # Call the function
        key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steg, plugboard = (
            parse_arguments()
        )

        # Assertions
        self.assertEqual(key_phrase, "test_key")
        self.assertEqual(mode, "encrypt")
        self.assertEqual(message, "test_message")
        self.assertEqual(cube_length, 5)
        self.assertEqual(num_rotors_to_make, 3)
        self.assertEqual(rotors_to_use, [1, 2, 3])
        self.assertTrue(should_use_steg)
        self.assertTrue(plugboard, ["AB", "CD"])
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["test_key", "test_encrypted_message"])
    @patch("cubigma.utils._read_and_validate_config")
    def test_parse_arguments_with_mode_decrypt(self, mock_read_and_validate_config, mock_input):
        """Test parse_arguments function with mode 'decrypt' and interactive inputs."""
        mock_read_and_validate_config.return_value = (
            4,  # cube_length
            2,  # num_rotors_to_make
            [0, 1],  # rotors_to_use
            "decrypt",  # mode
            False,  # should_use_steganography
            ["AB"],  # plugboard values
        )

        # Call the function
        key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steg, plugboard = (
            parse_arguments(mode="decrypt")
        )

        # Assertions
        self.assertEqual(key_phrase, "test_key")
        self.assertEqual(mode, "decrypt")
        self.assertEqual(message, "test_encrypted_message")  # Message is empty because it isn't provided
        self.assertEqual(cube_length, 4)
        self.assertEqual(num_rotors_to_make, 2)
        self.assertEqual(rotors_to_use, [0, 1])
        self.assertFalse(should_use_steg)
        self.assertTrue(plugboard, ["AB", "CD"])
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["cryptid", "message"])
    @patch("cubigma.utils._read_and_validate_config")
    def test_parse_arguments_invalid_mode(self, mock_read_and_validate_config, mock_input):
        """Test parse_arguments function with an invalid mode."""
        mock_read_and_validate_config.return_value = (0, 0, [], "invalid_mode", False, ["AB"])

        with self.assertRaises(ValueError) as context:
            parse_arguments()

        self.assertEqual(str(context.exception), "Unknown mode")
        mock_input.assert_called_once_with("Enter your key phrase: ")


class TestPrepStringForEncrypting(unittest.TestCase):

    def _fake_pad_chunk_with_rand_pad_symbols(self, chunk):
        """
        Mock implementation of the pad_chunk_with_rand_pad_symbols function
        Adds '*' symbols to the chunk until its length is LENGTH_OF_TRIO.
        """
        while len(chunk) < LENGTH_OF_TRIO:
            chunk += "*"
        return chunk

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_no_padding_needed(self, mock_pad):
        """Test when the input string is already a multiple of LENGTH_OF_TRIO."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "abc"
        expected_output = "abc"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_padding_needed_short(self, mock_pad):
        """Test when the input string length is not a multiple of LENGTH_OF_TRIO."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "ab"
        expected_output = "ab*"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_padding_needed_long(self, mock_pad):
        """Test when the input string length is not a multiple of LENGTH_OF_TRIO."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "abcde"
        expected_output = "abcde*"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_repeating_characters(self, mock_pad):
        """Test when the input string contains repeating characters in a chunk."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "aabbccdd"
        expected_output = "aabbccdd*"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_empty_string(self, mock_pad):
        """Test when the input string is empty."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        with self.assertRaises(ValueError):
            prep_string_for_encrypting("")

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_long_string(self, mock_pad):
        """Test a longer string with multiple chunks."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "abccdefghij"
        expected_output = "abccdefghij*"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)


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


class TestRotateSliceOfCube(unittest.TestCase):
    def setUp(self):
        self.cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["Y", "O", "P"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_x_axis_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "X"
        expected_rotate_dir = 1  # Clockwise
        slice_idx_to_rotate = 1
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['Y', 'O', 'P'],
            ['Y', 'O', 'P'],
            ['Y', 'O', 'P']
        ]
        mock_rotate.return_value = [
            ["Y", "Y", "Y"],
            ["O", "O", "O"],
            ["P", "P", "P"],
        ]
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["Y", "Y", "Y"], ["O", "O", "O"], ["P", "P", "P"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_x_axis_counter_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "X"
        expected_rotate_dir = -1  # Counter-clockwise
        slice_idx_to_rotate = 1
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['Y', 'O', 'P'],
            ['Y', 'O', 'P'],
            ['Y', 'O', 'P']
        ]
        mock_rotate.return_value = [
            ["P", "P", "P"],
            ["O", "O", "O"],
            ["Y", "Y", "Y"],
        ]
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["P", "P", "P"], ["O", "O", "O"], ["Y", "Y", "Y"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_y_axis_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "Y"
        expected_rotate_dir = 1  # Clockwise
        slice_idx_to_rotate = 0
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['R', 'G', 'B'],
            ['Y', 'O', 'P'],
            ['W', 'K', 'M']
        ]
        mock_rotate.return_value = [
            ["W", "Y", "R"],
            ["K", "O", "G"],
            ["M", "P", "B"],
        ]
        expected_cube = [
            [["W", "Y", "R"], ["R", "G", "B"], ["R", "G", "B"]],
            [["K", "O", "G"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["M", "P", "B"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_y_axis_counter_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "Y"
        expected_rotate_dir = -1  # Counter-clockwise
        slice_idx_to_rotate = 0
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['R', 'G', 'B'],
            ['Y', 'O', 'P'],
            ['W', 'K', 'M']
        ]
        mock_rotate.return_value = [
            ["B", "P", "M"],
            ["G", "O", "K"],
            ["R", "Y", "W"],
        ]
        expected_cube = [
            [["B", "P", "M"], ["R", "G", "B"], ["R", "G", "B"]],
            [["G", "O", "K"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["R", "Y", "W"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_z_axis_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "Z"
        expected_rotate_dir = 1  # Clockwise
        slice_idx_to_rotate = 2
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['B', 'B', 'B'],
            ['P', 'P', 'P'],
            ['M', 'M', 'M']
        ]
        mock_rotate.return_value = [
            ["M", "P", "B"],
            ["M", "P", "B"],
            ["M", "P", "B"],
        ]
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "P"], ["R", "G", "M"]],
            [["Y", "O", "B"], ["Y", "O", "P"], ["Y", "O", "M"]],
            [["W", "K", "B"], ["W", "K", "P"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)

    @patch("cubigma.utils.get_independently_deterministic_random_rotor_info")
    @patch("cubigma.utils._rotate_2d_array")
    def test_rotate_z_axis_counter_clockwise(self, mock_rotate, mock_random_rotor_info):
        # Arrange
        expected_axis = "Z"
        expected_rotate_dir = -1  # Counter-clockwise
        slice_idx_to_rotate = 2
        test_seed = "test_seed"
        mock_random_rotor_info.return_value = expected_axis, expected_rotate_dir, slice_idx_to_rotate
        expected_frame = [
            ['B', 'B', 'B'],
            ['P', 'P', 'P'],
            ['M', 'M', 'M']
        ]
        mock_rotate.return_value = [
            ["B", "P", "M"],
            ["B", "P", "M"],
            ["B", "P", "M"],
        ]
        expected_cube = [
            [["R", "G", "M"], ["R", "G", "P"], ["R", "G", "B"]],
            [["Y", "O", "M"], ["Y", "O", "P"], ["Y", "O", "B"]],
            [["W", "K", "M"], ["W", "K", "P"], ["W", "K", "B"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, test_seed)

        # Assert
        self.assertEqual(result_cube, expected_cube)
        mock_random_rotor_info.assert_called_once_with(test_seed, ["X", "Y", "Z"], [-1, 1], len(self.cube) - 1)
        mock_rotate.assert_called_once_with(expected_frame, expected_rotate_dir)


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
        self.assertEqual(split_to_human_readable_symbols("b̂c̃d̄"), ["b̂", "c̃", "d̄"])

        self.assertEqual(split_to_human_readable_symbols("é́👍🏽🎉"), ["é́", "👍🏽", "🎉"])

    def test_mixed_grapheme_clusters(self):
        """Test input with mixed grapheme clusters (combining marks and emojis)."""
        self.assertEqual(split_to_human_readable_symbols("👩‍❤️‍💋‍👨á👍🏽"), ["👩‍❤️‍💋‍👨", "á", "👍🏽"])

    def test_invalid_input_length(self):
        """Test input with invalid user-perceived lengths."""
        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("ab")  # 2 graphemes

        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("abcd")  # 4 graphemes

        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("b̂c̃d̄e")  # 4 graphemes

    def test_empty_string(self):
        """Test an empty string input, which should raise an error."""
        with self.assertRaises(ValueError):
            split_to_human_readable_symbols("")

    def test_non_string_input(self):
        """Test non-string input, which should raise a TypeError."""
        with self.assertRaises(TypeError):
            split_to_human_readable_symbols(None)  # noqa

        with self.assertRaises(TypeError):
            split_to_human_readable_symbols(123)  # noqa

    def test_valid_combining_characters(self):
        """Test valid input with combining characters to form graphemes."""
        self.assertEqual(split_to_human_readable_symbols("ôũī"), ["ô", "ũ", "ī"])


class TestUserPerceivedLength(unittest.TestCase):
    def test_basic_text(self):
        self.assertEqual(_user_perceived_length("hello"), 5)
        self.assertEqual(_user_perceived_length(""), 0)
        self.assertEqual(_user_perceived_length("a"), 1)

    def test_emojis(self):
        self.assertEqual(_user_perceived_length("🙂"), 1)
        self.assertEqual(_user_perceived_length("🙂🙂"), 2)

    def test_surrogate_pairs(self):
        self.assertEqual(_user_perceived_length("👨‍👩‍👧‍👦"), 1)  # Family emoji
        self.assertEqual(_user_perceived_length("👩‍❤️‍💋‍👨"), 1)  # Couple kissing emoji

    def test_combining_characters(self):
        self.assertEqual(_user_perceived_length("á"), 1)  # "á" as 'a' + combining acute accent
        self.assertEqual(_user_perceived_length("éé"), 2)  # Two "é"
        self.assertEqual(_user_perceived_length("é́"), 1)  # One "e" with two combining marks

    def test_mixed_content(self):
        self.assertEqual(_user_perceived_length("hello🙂"), 6)
        self.assertEqual(_user_perceived_length("🙂á"), 2)
        self.assertEqual(_user_perceived_length("🙂👩‍❤️‍💋‍👨"), 2)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
