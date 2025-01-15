# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch
import json
import unittest

from cubigma.utils import (
    LENGTH_OF_QUARTET,
    generate_cube_from_symbols,
    generate_plugboard,
    generate_rotors,
    get_chars_for_coordinates,
    get_opposite_corners,
    pad_chunk,
    parse_arguments,
    prep_string_for_encrypting,
    read_config,
    remove_duplicate_letters,
    rotate_slice_of_cube,
    sanitize,
    split_to_human_readable_symbols,
    _user_perceived_length,
)


class TestGenerateCubeFromSymbols(unittest.TestCase):
    def setUp(self):
        # Common test setup for symbols
        self.symbols = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]

    def test_generate_cube_valid_input(self):
        """Test cube generation with valid input."""
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 3

        expected_output = [[["a", "b", "c"], ["d", "e", "f"]], [["g", "h", "i"], ["j", "k", "l"]]]

        result = generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)
        self.assertEqual(result, expected_output)

    def test_generate_cube_edge_case_single_block(self):
        """Test cube generation with only one block."""
        num_blocks = 1
        lines_per_block = 2
        symbols_per_line = 3

        expected_output = [[["a", "b", "c"], ["d", "e", "f"]]]

        result = generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)
        self.assertEqual(result, expected_output)

    def test_generate_cube_invalid_symbols_length(self):
        """Test failure when symbols length does not match required input dimensions."""
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 4

        with self.assertRaises(ValueError) as context:
            generate_cube_from_symbols(self.symbols, num_blocks, lines_per_block, symbols_per_line)

        self.assertEqual(str(context.exception), "Something has failed")

    def test_generate_cube_escape_characters(self):
        """Test cube generation with escape characters in symbols."""
        symbols_with_escape = ["a", "\\", "\n", "b", "\t", "c", "d", "e", "f", "g", "h", "i"]
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 3

        expected_output = [[["a", "\\\\", "\\n"], ["b", "\\t", "c"]], [["d", "e", "f"], ["g", "h", "i"]]]

        result = generate_cube_from_symbols(symbols_with_escape, num_blocks, lines_per_block, symbols_per_line)
        self.assertEqual(result, expected_output)

    def test_generate_cube_empty_symbols(self):
        """Test cube generation with empty symbols list."""
        symbols = []
        num_blocks = 0
        lines_per_block = 0
        symbols_per_line = 0

        expected_output = []

        result = generate_cube_from_symbols(symbols, num_blocks, lines_per_block, symbols_per_line)
        self.assertEqual(result, expected_output)


class TestGeneratePlugboard(unittest.TestCase):

    def test_valid_plugboard_values(self):
        plugboard_values = ["AB", "CD", "EF"]
        expected_output = {"A": "B", "B": "A", "C": "D", "D": "C", "E": "F", "F": "E"}
        result = generate_plugboard(plugboard_values)
        self.assertEqual(result, expected_output)

    def test_empty_plugboard_values(self):
        plugboard_values = []
        expected_output = {}
        result = generate_plugboard(plugboard_values)
        self.assertEqual(result, expected_output)

    def test_invalid_plugboard_value_length(self):
        plugboard_values = ["A", "BCD", "EF"]
        with self.assertRaises(ValueError) as context:
            generate_plugboard(plugboard_values)
        self.assertIn("Plugboard values are expected to all be pairs of symbols.", str(context.exception))

    def test_duplicate_symbols(self):
        plugboard_values = ["AB", "AC"]
        with self.assertRaises(ValueError):
            generate_plugboard(plugboard_values)

    def test_non_string_symbols(self):
        plugboard_values = [123, "AB"]
        with self.assertRaises(TypeError):
            generate_plugboard(plugboard_values)


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

    def test_missing_key_phrase(self):
        """Test function raises error on missing or invalid key phrase."""
        with self.assertRaises(ValueError):
            generate_rotors(
                "",
                self.valid_cube,
                num_rotors_to_make=self.num_rotors_to_make,
                rotors_to_use=self.rotors_to_use,
                orig_key_length=42,
            )

    def test_invalid_num_rotors_to_make(self):
        """Test function raises error on invalid num_rotors_to_make."""
        with self.assertRaises(ValueError):
            generate_rotors(
                self.valid_key,
                self.valid_cube,
                num_rotors_to_make=-1,
                rotors_to_use=self.rotors_to_use,
                orig_key_length=42,
            )

    def test_invalid_rotors_to_use_values(self):
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

    def test_invalid_rotors_to_use_not_list(self):
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

    def test_invalid_cube(self):
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

    def test_invalid_key_length(self):
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
        result = get_chars_for_coordinates(coordinate, test_rotor)

        # Assert
        self.assertEqual(expected_result, result)

    def test_get_chars_for_invalid_coordinates(self):
        # Arrange
        test_rotor = [[["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]]
        coordinate = (1, 0, 2)

        # Act & Assert
        with self.assertRaises(IndexError):
            get_chars_for_coordinates(coordinate, test_rotor)


class TestGetOppositeCorners(unittest.TestCase):
    def setUp(self):
        self.num_blocks = 10
        self.lines_per_block = 10
        self.symbols_per_line = 10
        self.key_phrase = "testkey"
        self.num_quartets_encoded = 1

    def test_valid_input(self):
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 1)
        point_3 = (0, 1, 0)
        point_4 = (0, 1, 1)

        result = get_opposite_corners(
            point_1,
            point_2,
            point_3,
            point_4,
            self.num_blocks,
            self.lines_per_block,
            self.symbols_per_line,
            self.key_phrase,
            self.num_quartets_encoded,
        )

        self.assertEqual(len(result), 4)
        for point in result:
            self.assertIsInstance(point, tuple)
            self.assertEqual(len(point), 3)

    def test_non_unique_points(self):
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 0)  # Duplicate
        point_3 = (0, 1, 0)
        point_4 = (0, 1, 1)

        with self.assertRaises(ValueError):
            get_opposite_corners(
                point_1,
                point_2,
                point_3,
                point_4,
                self.num_blocks,
                self.lines_per_block,
                self.symbols_per_line,
                self.key_phrase,
                self.num_quartets_encoded,
            )

    # def test_points_outside_bounds(self):
    #     point_1 = (-1, 0, 0)
    #     point_2 = (0, 11, 1)
    #     point_3 = (0, 1, -1)
    #     point_4 = (0, 1, 1)
    #
    #     with self.assertRaises(ValueError):
    #         get_opposite_corners(
    #             point_1, point_2, point_3, point_4,
    #             self.num_blocks, self.lines_per_block, self.symbols_per_line,
    #             self.key_phrase, self.num_quartets_encoded
    #         )

    def test_key_phrase_affects_result(self):
        point_1 = (0, 0, 0)
        point_2 = (0, 0, 1)
        point_3 = (0, 1, 0)
        point_4 = (0, 1, 1)

        result_1 = get_opposite_corners(
            point_1,
            point_2,
            point_3,
            point_4,
            self.num_blocks,
            self.lines_per_block,
            self.symbols_per_line,
            "key1",
            self.num_quartets_encoded,
        )

        result_2 = get_opposite_corners(
            point_1,
            point_2,
            point_3,
            point_4,
            self.num_blocks,
            self.lines_per_block,
            self.symbols_per_line,
            "key2",
            self.num_quartets_encoded,
        )

        self.assertNotEqual(result_1, result_2)


class TestPadChunk(unittest.TestCase):
    def setUp(self):
        self.chunk_order_number = 2
        self.rotor = [[["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]]]

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    @patch("cubigma.utils._get_random_noise_chunk")
    @patch("cubigma.utils._get_prefix_order_number_quartet")
    def test_pad_chunk_even_length(
        self, mock_get_prefix_order_number_quartet, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols
    ):
        # Arrange
        mock_get_prefix_order_number_quartet.return_value = "ORDR"
        mock_get_random_noise_chunk.return_value = "XXXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "TEST"
        expected_result = "ORDRTESTXXXXXXXXXXXX"
        padded_chunk_length = 16

        # Act
        result = pad_chunk(test_chunk, padded_chunk_length, self.chunk_order_number, self.rotor)

        # Assert
        self.assertTrue(result.startswith("ORDR"))
        self.assertEqual(expected_result, result)
        self.assertEqual(len(result[4:]), padded_chunk_length)
        mock_get_prefix_order_number_quartet.assert_called_once_with(self.chunk_order_number)
        mock_get_random_noise_chunk.assert_called()
        mock_pad_chunk_with_rand_pad_symbols.assert_not_called()

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    @patch("cubigma.utils._get_random_noise_chunk")
    @patch("cubigma.utils._get_prefix_order_number_quartet")
    def test_pad_chunk_short_length(
        self, mock_get_prefix_order_number_quartet, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols
    ):
        # Arrange
        mock_get_prefix_order_number_quartet.return_value = "ORDR"
        mock_get_random_noise_chunk.return_value = "XXXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "TES"
        expected_result = "ORDRTESPXXXXXXXXXXXX"
        padded_chunk_length = 16

        # Act
        result = pad_chunk(test_chunk, padded_chunk_length, self.chunk_order_number, self.rotor)

        # Assert
        self.assertTrue(result.startswith("ORDR"))
        self.assertEqual(expected_result, result)
        self.assertEqual(len(result[4:]), padded_chunk_length)
        mock_get_prefix_order_number_quartet.assert_called_once_with(self.chunk_order_number)
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
        Adds '*' symbols to the chunk until its length is LENGTH_OF_QUARTET.
        """
        while len(chunk) < LENGTH_OF_QUARTET:
            chunk += "*"
        return chunk

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_no_padding_needed(self, mock_pad):
        """Test when the input string is already a multiple of LENGTH_OF_QUARTET."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "abcd"
        expected_output = "abcd"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_padding_needed(self, mock_pad):
        """Test when the input string length is not a multiple of LENGTH_OF_QUARTET."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "abc"
        expected_output = "abc*"
        result = prep_string_for_encrypting(input_message)
        self.assertEqual(result, expected_output)

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    def test_repeating_characters(self, mock_pad):
        """Test when the input string contains repeating characters in a chunk."""
        mock_pad.side_effect = self._fake_pad_chunk_with_rand_pad_symbols
        input_message = "aabbcc"
        expected_output = "a***ab**bc**c***"
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
        expected_output = "abc*cdefghij"
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


class TestRotateSliceOfCube(unittest.TestCase):
    def setUp(self):
        self.cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["Y", "O", "P"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_x_axis_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["X", 1]  # Choose X-axis, clockwise rotation
        mock_randint.return_value = 1  # Rotate slice index 1
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["Y", "Y", "Y"], ["O", "O", "O"], ["P", "P", "P"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_x_axis_counter_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["X", -1]  # Choose X-axis, clockwise rotation
        mock_randint.return_value = 1  # Rotate slice index 1
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "B"], ["R", "G", "B"]],
            [["P", "P", "P"], ["O", "O", "O"], ["Y", "Y", "Y"]],
            [["W", "K", "M"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_y_axis_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["Y", 1]  # Choose Y-axis, counterclockwise rotation
        test_slice_idx = 0
        mock_randint.return_value = test_slice_idx  # Rotate slice index 0
        expected_cube = [
            [["W", "Y", "R"], ["R", "G", "B"], ["R", "G", "B"]],
            [["K", "O", "G"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["M", "P", "B"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_y_axis_counter_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["Y", -1]  # Choose Y-axis, counterclockwise rotation
        test_slice_idx = 0
        mock_randint.return_value = test_slice_idx  # Rotate slice index 0
        expected_cube = [
            [["B", "P", "M"], ["R", "G", "B"], ["R", "G", "B"]],
            [["G", "O", "K"], ["Y", "O", "P"], ["Y", "O", "P"]],
            [["R", "Y", "W"], ["W", "K", "M"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_z_axis_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["Z", 1]  # Choose Z-axis, clockwise rotation
        mock_randint.return_value = 2  # Rotate slice index 2
        expected_cube = [
            [["R", "G", "B"], ["R", "G", "P"], ["R", "G", "M"]],
            [["Y", "O", "B"], ["Y", "O", "P"], ["Y", "O", "M"]],
            [["W", "K", "B"], ["W", "K", "P"], ["W", "K", "M"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)

    @patch("random.choice")
    @patch("random.randint")
    def test_rotate_z_axis_counter_clockwise(self, mock_randint, mock_choice):
        # Arrange
        mock_choice.side_effect = ["Z", -1]  # Choose Z-axis, clockwise rotation
        mock_randint.return_value = 2  # Rotate slice index 2
        expected_cube = [
            [["R", "G", "M"], ["R", "G", "P"], ["R", "G", "B"]],
            [["Y", "O", "M"], ["Y", "O", "P"], ["Y", "O", "B"]],
            [["W", "K", "M"], ["W", "K", "P"], ["W", "K", "B"]],
        ]

        # Act
        result_cube = rotate_slice_of_cube(self.cube, "test_seed")

        # Assert
        self.assertEqual(result_cube, expected_cube)


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
