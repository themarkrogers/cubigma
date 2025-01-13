# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from copy import deepcopy
from unittest.mock import patch
import base64
import json
import os
import unittest

from cubigma.utils import (
    NOISE_SYMBOL,
    LENGTH_OF_QUARTET,
    generate_reflector,
    generate_rotors,
    get_chars_for_coordinates,
    get_opposite_corners,
    index_to_quartet,
    pad_chunk,
    parse_arguments,
    prep_string_for_encrypting,
    quartet_to_index,
    read_config,
    remove_duplicate_letters,
    sanitize,
    split_to_human_readable_symbols,
    strengthen_key,
    user_perceived_length,
)
from cubigma.utils import (
    _find_symbol,
    _get_flat_index,
    _get_next_corner_choices,
    _get_prefix_order_number_quartet,
    _get_random_noise_chunk,
    _is_valid_coord,
    _move_letter_to_center,
    _move_letter_to_front,
    _move_symbol_in_3d_grid,
    _pad_chunk_with_rand_pad_symbols,
    _read_and_validate_config,
    _shuffle_cube_with_key_phrase,
    _split_key_into_parts,
)


# Testing Private Functions


class TestFindSymbol(unittest.TestCase):
    def setUp(self):
        # Example 3x3x3 playfair cube
        self.playfair_cube = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]

    def test_find_symbol_valid(self):
        # Test cases for valid symbols
        self.assertEqual(_find_symbol("A", self.playfair_cube), (0, 0, 0))
        self.assertEqual(_find_symbol("E", self.playfair_cube), (0, 1, 1))
        self.assertEqual(_find_symbol("R", self.playfair_cube), (1, 2, 2))
        self.assertEqual(_find_symbol("Z", self.playfair_cube), (2, 2, 1))

    def test_find_symbol_not_found(self):
        # Test for a symbol that is not in the cube
        with self.assertRaises(ValueError) as context:
            _find_symbol("1", self.playfair_cube)
        self.assertEqual(str(context.exception), "Symbol '1' not found in playfair_cube.")

    def test_find_symbol_edge_cases(self):
        # Test for edge cases like last element
        self.assertEqual(_find_symbol("0", self.playfair_cube), (2, 2, 2))
        self.assertEqual(_find_symbol("Z", self.playfair_cube), (2, 2, 1))
        self.assertEqual(_find_symbol("X", self.playfair_cube), (2, 1, 2))
        self.assertEqual(_find_symbol("R", self.playfair_cube), (1, 2, 2))


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


class TestGetFlatIndex(unittest.TestCase):
    def test_basic_case(self):
        """Test basic case with typical inputs."""
        self.assertEqual(_get_flat_index(2, 3, 4, 5, 6), 79)

    def test_zero_coordinates(self):
        """Test when x, y, or z is zero."""
        self.assertEqual(_get_flat_index(0, 0, 0, 4, 5), 0)
        self.assertEqual(_get_flat_index(0, 1, 2, 4, 5), 6)
        self.assertEqual(_get_flat_index(1, 0, 2, 4, 5), 22)
        self.assertEqual(_get_flat_index(1, 2, 0, 4, 5), 28)

    def test_large_values(self):
        """Test with large values to ensure no overflow issues."""
        self.assertEqual(_get_flat_index(100, 200, 300, 400, 500), 20_080_300)

    def test_edge_case_sizes(self):
        """Test edge cases where size_x or size_y is 1."""
        self.assertEqual(_get_flat_index(1, 2, 3, 1, 1), 6)
        self.assertEqual(_get_flat_index(1, 2, 3, 1, 5), 10)
        self.assertEqual(_get_flat_index(1, 2, 3, 4, 1), 15)

    def test_negative_coordinates(self):
        """Test with negative coordinates to ensure proper handling."""
        self.assertEqual(_get_flat_index(-1, 2, 3, 4, 5), -9)
        self.assertEqual(_get_flat_index(1, -2, 3, 4, 5), 15)
        self.assertEqual(_get_flat_index(1, 2, -3, 4, 5), 25)

    def test_invalid_sizes(self):
        """Test with invalid sizes to ensure proper handling."""
        with self.assertRaises(ValueError):
            _get_flat_index(1, 2, 3, 0, 5)
        with self.assertRaises(ValueError):
            _get_flat_index(1, 2, 3, 4, 0)
        with self.assertRaises(ValueError):
            _get_flat_index(1, 2, 3, -4, 5)
        with self.assertRaises(ValueError):
            _get_flat_index(1, 2, 3, 4, -5)


class TestGetNextCornerChoices(unittest.TestCase):
    def test_deterministic_output(self):
        """Test that the function produces deterministic outputs for the same inputs."""
        key_phrase = "test_key"
        num_quartets_encoded = 5

        result1 = _get_next_corner_choices(key_phrase, num_quartets_encoded)
        result2 = _get_next_corner_choices(key_phrase, num_quartets_encoded)

        self.assertEqual(result1, result2, "The function should produce the same output for the same inputs.")

    def test_output_within_range(self):
        """Test that the output values are within the range [0-7]."""
        key_phrase = "range_test"
        num_quartets_encoded = 10

        result = _get_next_corner_choices(key_phrase, num_quartets_encoded)

        self.assertEqual(len(result), 4, "The function should return exactly 4 integers.")
        self.assertTrue(all(0 <= x <= 7 for x in result), "All integers should be within the range 0-7.")

    def test_different_inputs_produce_different_outputs(self):
        """Test that different inputs produce different outputs."""
        key_phrase = "unique_test"

        result1 = _get_next_corner_choices(key_phrase, 1)
        result2 = _get_next_corner_choices(key_phrase, 2)

        self.assertNotEqual(result1, result2, "Different num_quartets_encoded values should produce different outputs.")

    def test_different_key_phrases_produce_different_outputs(self):
        """Test that different key phrases produce different outputs."""
        num_quartets_encoded = 1

        result1 = _get_next_corner_choices("key_phrase_1", num_quartets_encoded)
        result2 = _get_next_corner_choices("key_phrase_2", num_quartets_encoded)

        self.assertNotEqual(result1, result2, "Different key phrases should produce different outputs.")


class TestGetPrefixOrderNumberQuartet(unittest.TestCase):
    def test_valid_order_number(self):
        """Test that a valid single-digit order number returns a quartet of symbols including the order number."""
        order_number = 5
        result = _get_prefix_order_number_quartet(order_number)

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
            _get_prefix_order_number_quartet(10)  # Not a single-digit number

        with self.assertRaises(AssertionError):
            _get_prefix_order_number_quartet(-1)  # Negative number

        with self.assertRaises(AssertionError):
            _get_prefix_order_number_quartet(123)  # Multiple digits

    def test_randomness(self):
        """Test that the function produces different outputs for the same input due to shuffling."""
        order_number = 3
        results = {_get_prefix_order_number_quartet(order_number) for _ in range(100)}

        # Verify that we have multiple unique outputs, indicating randomness
        self.assertGreater(len(results), 1, "Function does not produce randomized outputs")


class TestGetRandomNoiseChunk(unittest.TestCase):
    def setUp(self):
        self.rotor = [
            [
                ["A", "B", "C"],
                ["D", "E", "F"],
                ["G", "H", "I"],
            ],
            [
                ["J", "K", "L"],
                ["M", "N", "O"],
                ["P", "Q", "R"],
            ],
            [
                ["S", "T", "U"],
                ["V", "W", "X"],
                ["Y", "Z", "0"],
            ],
        ]

    @patch("random.randint")
    @patch("random.shuffle", lambda x: None)  # Prevent shuffle for predictable output
    def test_output_length(self, mock_randint):
        """Test that the function output has the correct length."""
        mock_randint.side_effect = [0, 0, 0, 1, 1, 1, 2, 2, 2]  # Mock coordinates
        result = _get_random_noise_chunk(self.rotor)
        self.assertEqual(len(result), LENGTH_OF_QUARTET)

    @patch("random.randint")
    def test_includes_noise_symbol(self, mock_randint):
        """Test that the output includes the NOISE_SYMBOL."""
        mock_randint.side_effect = [0, 0, 0, 1, 1, 1, 2, 2, 2]
        result = _get_random_noise_chunk(self.rotor)
        self.assertIn(NOISE_SYMBOL, result)

    @patch("random.randint")
    def test_unique_symbols_in_output(self, mock_randint):
        """Test that the output contains unique symbols."""
        mock_randint.side_effect = [0, 0, 0, 1, 1, 1, 2, 2, 2]
        result = _get_random_noise_chunk(self.rotor)
        self.assertEqual(len(set(result)), LENGTH_OF_QUARTET)

    @patch("random.randint")
    def test_handles_non_uniform_rotor(self, mock_randint):
        """Test that the function handles a rotor with varying dimensions."""
        non_uniform_rotor = [
            [["A", "B"]],
            [["C", "D", "E"]],
            [["F"]],
        ]
        mock_randint.side_effect = [0, 0, 0, 1, 0, 0, 2, 0, 0]
        result = _get_random_noise_chunk(non_uniform_rotor)
        self.assertEqual(len(result), LENGTH_OF_QUARTET)


class TestIsValidCoord(unittest.TestCase):
    def test_valid_coordinates(self):
        grid = [[[0 for _ in range(3)] for _ in range(4)] for _ in range(5)]  # 5x4x3 grid
        self.assertTrue(_is_valid_coord((0, 0, 0), grid))  # Lower boundary
        self.assertTrue(_is_valid_coord((4, 3, 2), grid))  # Upper boundary
        self.assertTrue(_is_valid_coord((2, 2, 1), grid))  # Middle of the grid

    def test_invalid_x_coordinate(self):
        grid = [[[0 for _ in range(3)] for _ in range(4)] for _ in range(5)]  # 5x4x3 grid
        self.assertFalse(_is_valid_coord((-1, 0, 0), grid))  # Negative x
        self.assertFalse(_is_valid_coord((5, 0, 0), grid))  # x outside upper limit

    def test_invalid_y_coordinate(self):
        grid = [[[0 for _ in range(3)] for _ in range(4)] for _ in range(5)]  # 5x4x3 grid
        self.assertFalse(_is_valid_coord((0, -1, 0), grid))  # Negative y
        self.assertFalse(_is_valid_coord((0, 4, 0), grid))  # y outside upper limit

    def test_invalid_z_coordinate(self):
        grid = [[[0 for _ in range(3)] for _ in range(4)] for _ in range(5)]  # 5x4x3 grid
        self.assertFalse(_is_valid_coord((0, 0, -1), grid))  # Negative z
        self.assertFalse(_is_valid_coord((0, 0, 3), grid))  # z outside upper limit

    def test_empty_grid(self):
        grid = []  # Empty grid
        self.assertFalse(_is_valid_coord((0, 0, 0), grid))  # Any coordinate is invalid

    def test_non_uniform_grid(self):
        grid = [
            [[0, 1], [2, 3]],  # 2x2x2 grid in first dimension
            [[4, 5, 6], [7, 8, 9]],  # 2x2x3 grid in second dimension
        ]
        self.assertTrue(_is_valid_coord((0, 0, 1), grid))  # Valid in first grid
        self.assertFalse(_is_valid_coord((1, 0, 2), grid))  # Invalid in second grid (z exceeds limit)


class TestMoveLetterToCenter(unittest.TestCase):

    @patch("cubigma.utils._move_symbol_in_3d_grid")
    def test_move_letter_to_center_with_even_dimensions(self, mock_move_symbol_in_3d_grid):
        # Arrange
        expected_return_value = [
            [["A", "B", "C", "D"], ["E", "F", "G", "H"], ["I", "J", "K", "L"], ["M", "N", "O", "P"]],
            [["Q", "R", "S", "T"], ["U", "V", "W", "X"], ["Y", "Z", "1", "2"], ["3", "4", "5", "6"]],
            [["7", "8", "9", "0"], ["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k", "l"]],
            [["m", "n", "o", "p"], ["q", "r", "s", "t"], ["u", "v", "w", "x"], ["y", "z", "!", "@"]],
        ]
        mock_move_symbol_in_3d_grid.return_value = expected_return_value
        test_symbol = "R"
        test_cube = [
            expected_return_value[3],
            expected_return_value[2],
            expected_return_value[1],
            expected_return_value[0],
        ]

        # Act
        result = _move_letter_to_center(test_symbol, test_cube)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((2, 0, 1), (2, 2, 2), test_cube)

    @patch("cubigma.utils._move_symbol_in_3d_grid")
    def test_move_letter_to_center_with_odd_dimensions(self, mock_move_symbol_in_3d_grid):
        # Arrange
        expected_return_value = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "1"]],
        ]
        mock_move_symbol_in_3d_grid.return_value = expected_return_value
        test_symbol = "R"
        test_cube = [expected_return_value[2], expected_return_value[1], expected_return_value[0]]

        # Act
        result = _move_letter_to_center(test_symbol, test_cube)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((1, 2, 2), (1, 1, 1), test_cube)


class TestMoveLetterToFront(unittest.TestCase):

    @patch("cubigma.utils._move_symbol_in_3d_grid")
    def test_move_letter_to_front(self, mock_move_symbol_in_3d_grid):
        # Arrange
        expected_return_value = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "1"]],
        ]
        mock_move_symbol_in_3d_grid.return_value = expected_return_value
        test_symbol = "R"
        test_cube = [expected_return_value[2], expected_return_value[1], expected_return_value[0]]

        # Act
        result = _move_letter_to_front(test_symbol, test_cube)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((1, 2, 2), (0, 0, 0), test_cube)


class TestMoveSymbolIn3DSpace(unittest.TestCase):

    def setUp(self):
        # Set up a 3x3x3 grid for testing
        self.grid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
        ]

    def test_valid_move_forward(self):
        # Test moving a symbol forward in the grid
        coord1 = (0, 0, 0)
        coord2 = (2, 1, 0)
        result = _move_symbol_in_3d_grid(coord1, coord2, self.grid)
        self.assertEqual(result[0][0][0], "B")
        self.assertEqual(result[0][0][1], "C")
        self.assertEqual(result[2][1][0], "A")
        self.assertEqual(result[2][2][2], "0")

    def test_valid_move_backward(self):
        # Test moving a symbol backward in the grid
        coord1 = (2, 1, 0)
        coord2 = (0, 0, 0)
        result = _move_symbol_in_3d_grid(coord1, coord2, self.grid)
        self.assertEqual(result[0][0][0], "V")
        self.assertEqual(result[0][0][1], "A")
        self.assertEqual(result[2][1][0], "U")
        self.assertEqual(result[2][2][2], "0")

    def test_move_to_same_position(self):
        # Test moving a symbol to the same position
        coord1 = (1, 1, 1)
        coord2 = (1, 1, 1)
        result = _move_symbol_in_3d_grid(coord1, coord2, self.grid)
        self.assertEqual(result, self.grid)

    def test_invalid_coord1(self):
        # Test when coord1 is out of bounds
        coord1 = (3, 0, 0)
        coord2 = (0, 0, 0)
        with self.assertRaises(ValueError):
            _move_symbol_in_3d_grid(coord1, coord2, self.grid)

    def test_invalid_coord2(self):
        # Test when coord2 is out of bounds
        coord1 = (0, 0, 0)
        coord2 = (3, 0, 0)
        with self.assertRaises(ValueError):
            _move_symbol_in_3d_grid(coord1, coord2, self.grid)

    def test_large_grid_move(self):
        # Test a larger grid
        large_grid = [[[f"{x}{y}{z}" for z in range(5)] for y in range(5)] for x in range(5)]
        coord1 = (2, 2, 2)
        coord2 = (3, 3, 3)
        result = _move_symbol_in_3d_grid(coord1, coord2, large_grid)
        self.assertEqual(result[3][3][3], "222")
        self.assertNotEqual(result[2][2][2], "222")

    def test_move_symbol_in_3d_grid_with_valid_coords(self):
        # Arrange & Act
        result = _move_symbol_in_3d_grid((0, 0, 0), (1, 1, 1), self.grid)

        # Assert
        self.assertNotEqual(self.grid, result, "Failed to manipulate cube")


class TestReadAndValidateConfig(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "LENGTH_OF_CUBE": 7,
            "NUMBER_OF_ROTORS_TO_GENERATE": 10,
            "ROTORS_TO_USE": [1, 2, 3],
            "ENCRYPT_OR_DECRYPT": "ENCRYPT",
            "ALSO_USE_STEGANOGRAPHY": True,
        }

    @patch("cubigma.utils.read_config")
    def test_valid_config(self, mock_read_config):
        mock_read_config.return_value = self.valid_config
        result = _read_and_validate_config()
        self.assertEqual(result, (7, 10, [1, 2, 3], "ENCRYPT", True))

    @patch("cubigma.utils.read_config")
    def test_missing_length_of_cube(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["LENGTH_OF_CUBE"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("LENGTH_OF_CUBE not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_length_of_cube_type(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["LENGTH_OF_CUBE"] = "3"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("LENGTH_OF_CUBE (in config.json) must have an integer value", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_invalid_length_of_cube(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["LENGTH_OF_CUBE"] = 3
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "LENGTH_OF_CUBE (in config.json) must be greater than 4 and lower than 12", str(context.exception)
        )

    @patch("cubigma.utils.read_config")
    def test_missing_num_rotors_to_make(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["NUMBER_OF_ROTORS_TO_GENERATE"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("NUMBER_OF_ROTORS_TO_GENERATE not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_num_rotors_to_make_type(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["NUMBER_OF_ROTORS_TO_GENERATE"] = "3"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "NUMBER_OF_ROTORS_TO_GENERATE (in config.json) must have an integer value", str(context.exception)
        )

    @patch("cubigma.utils.read_config")
    def test_invalid_num_rotors_to_make(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["NUMBER_OF_ROTORS_TO_GENERATE"] = -1
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("NUMBER_OF_ROTORS_TO_GENERATE (in config.json) must be greater than 0", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_missing_rotors_to_use(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["ROTORS_TO_USE"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ROTORS_TO_USE not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_rotors_to_use_type(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ROTORS_TO_USE"] = "[0, 1, 2]"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ROTORS_TO_USE (in config.json) must be a list of integers", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_rotors_to_use_values_1(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ROTORS_TO_USE"] = [1, "0", 2]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ROTORS_TO_USE (in config.json) contains a non-integer value at index: 1", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_rotors_to_use_values_2(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ROTORS_TO_USE"] = [2, 1, 42]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "OTORS_TO_USE (in config.json) all rotor values must be between 0 & the number of rotors generated",
            str(context.exception),
        )

    @patch("cubigma.utils.read_config")
    def test_duplicate_rotors(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ROTORS_TO_USE"] = [1, 1, 3]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ROTORS_TO_USE (in config.json) all rotor values must be unique", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_missing_mode(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["ENCRYPT_OR_DECRYPT"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ENCRYPT_OR_DECRYPT not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_mode_type(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ENCRYPT_OR_DECRYPT"] = True
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ENCRYPT_OR_DECRYPT (in config.json) must be a string", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_invalid_mode(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ENCRYPT_OR_DECRYPT"] = "INVALID_MODE"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "ENCRYPT_OR_DECRYPT (in config.json) must be either 'ENCRYPT' or 'DECRYPT'", str(context.exception)
        )

    @patch("cubigma.utils.read_config")
    def test_missing_steganography(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["ALSO_USE_STEGANOGRAPHY"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ALSO_USE_STEGANOGRAPHY not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_invalid_steganography(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["ALSO_USE_STEGANOGRAPHY"] = "true"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("ALSO_USE_STEGANOGRAPHY (in config.json) must be a boolean value", str(context.exception))


class TestShuffleCubeWithKeyPhrase(unittest.TestCase):
    def setUp(self):
        """Set up reusable test data."""
        self.key_phrase_1 = "securekey1"
        self.key_phrase_2 = "differentkey"

        self.orig_cube = [[["a", "b", "c"], ["d", "e", "f"]], [["g", "h", "i"], ["j", "k", "l"]]]

    def test_consistent_shuffling_with_same_key(self):
        """Test that shuffling with the same key gives consistent results."""
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube))
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube))
        self.assertEqual(shuffled_1, shuffled_2)

    def test_different_keys_produce_different_results(self):
        """Test that shuffling with different keys gives different results."""
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube))
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_2, deepcopy(self.orig_cube))
        self.assertNotEqual(shuffled_1, shuffled_2)

    def test_structure_preserved(self):
        """Test that the structure of the cube is preserved after shuffling."""
        shuffled = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube))
        # Ensure the top-level list length is preserved
        self.assertEqual(len(shuffled), len(self.orig_cube))
        for orig_outer, shuffled_outer in zip(self.orig_cube, shuffled):
            # Ensure the second-level list length is preserved
            self.assertEqual(len(shuffled_outer), len(orig_outer))
            for orig_inner, shuffled_inner in zip(orig_outer, shuffled_outer):
                # Ensure the third-level list length is preserved
                self.assertEqual(len(shuffled_inner), len(orig_inner))

    def test_no_side_effects(self):
        """Test that the original cube is not modified by the function."""
        orig_cube_copy = deepcopy(self.orig_cube)
        _ = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube))
        self.assertEqual(self.orig_cube, orig_cube_copy)


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


class TestGenerateReflector(unittest.TestCase):

    def test_reflector_pairs_correctly(self):
        """Test that the reflector maps quartets bidirectionally."""
        sanitized_key_phrase = "testkey"
        num_quartets = 10
        reflector = generate_reflector(sanitized_key_phrase, num_quartets)

        for key, value in reflector.items():
            self.assertEqual(reflector[value], key)

    def test_deterministic_output(self):
        """Test that the function generates deterministic output for the same key."""
        sanitized_key_phrase = "testkey"
        num_quartets = 10
        reflector1 = generate_reflector(sanitized_key_phrase, num_quartets)
        reflector2 = generate_reflector(sanitized_key_phrase, num_quartets)

        self.assertEqual(reflector1, reflector2)

    def test_randomized_output_with_different_keys(self):
        """Test that the function generates different outputs for different keys."""
        sanitized_key_phrase1 = "key1"
        sanitized_key_phrase2 = "key2"
        num_quartets = 10
        reflector1 = generate_reflector(sanitized_key_phrase1, num_quartets)
        reflector2 = generate_reflector(sanitized_key_phrase2, num_quartets)

        self.assertNotEqual(reflector1, reflector2)

    def test_even_number_of_quartets(self):
        """Test that the function raises an error for odd number of quartets."""
        sanitized_key_phrase = "testkey"
        num_quartets = 9  # Odd number of quartets
        with self.assertRaises(IndexError):
            generate_reflector(sanitized_key_phrase, num_quartets)

    def test_empty_key(self):
        """Test that an empty key produces valid but deterministic results."""
        sanitized_key_phrase = ""
        num_quartets = 10
        reflector = generate_reflector(sanitized_key_phrase, num_quartets)

        self.assertIsInstance(reflector, dict)
        self.assertEqual(len(reflector), num_quartets)

    def test_large_number_of_quartets(self):
        """Test that the function handles a large number of quartets."""
        sanitized_key_phrase = "largekey"
        num_quartets = 10000  # Large number of quartets
        reflector = generate_reflector(sanitized_key_phrase, num_quartets)

        self.assertIsInstance(reflector, dict)
        self.assertEqual(len(reflector), num_quartets)
        for key, value in reflector.items():
            self.assertEqual(reflector[value], key)


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
        mock_shuffle.side_effect = lambda key, cube: cube  # Mock shuffle function

        result = generate_rotors(
            sanitized_key_phrase=self.valid_key,
            raw_cube=self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
        )

        self.assertEqual(len(result), len(self.rotors_to_use))
        for rotor in result:
            self.assertEqual(rotor, self.valid_cube)

    def test_missing_key_phrase(self):
        """Test function raises error on missing or invalid key phrase."""
        with self.assertRaises(ValueError):
            generate_rotors("", self.valid_cube, self.num_rotors_to_make, self.rotors_to_use)

    def test_invalid_num_rotors_to_make(self):
        """Test function raises error on invalid num_rotors_to_make."""
        with self.assertRaises(ValueError):
            generate_rotors(self.valid_key, self.valid_cube, -1, self.rotors_to_use)

    def test_invalid_rotors_to_use_values(self):
        """Test function raises error on invalid rotors_to_use."""
        invalid_rotors = [0, 5, 1, 1]  # Duplicate and out-of-range values
        with self.assertRaises(ValueError):
            generate_rotors(self.valid_key, self.valid_cube, self.num_rotors_to_make, invalid_rotors)

    def test_invalid_rotors_to_use_not_list(self):
        """Test function raises error on invalid rotors_to_use."""
        invalid_rotors = "[0, 5, 1, 1]"
        with self.assertRaises(ValueError):
            generate_rotors(self.valid_key, self.valid_cube, self.num_rotors_to_make, invalid_rotors)

    def test_invalid_cube(self):
        """Test function raises error on invalid rotors_to_use."""
        invalid_cube = [["AB", "CD"], ["EF", "GH"]]
        with self.assertRaises(ValueError):
            generate_rotors(self.valid_key, invalid_cube, self.num_rotors_to_make, self.rotors_to_use)

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_rotors_correct_count(self, mock_shuffle):
        """Test function generates the correct number of rotors."""
        mock_shuffle.side_effect = lambda key, cube: cube

        result = generate_rotors(
            sanitized_key_phrase=self.valid_key,
            raw_cube=self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
        )

        self.assertEqual(len(result), len(self.rotors_to_use))

    @patch("cubigma.utils._shuffle_cube_with_key_phrase")
    def test_deterministic_output(self, mock_shuffle):
        """Test function produces deterministic output for the same inputs."""
        mock_shuffle.side_effect = lambda key, cube: cube

        result1 = generate_rotors(
            sanitized_key_phrase=self.valid_key,
            raw_cube=self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
        )

        result2 = generate_rotors(
            sanitized_key_phrase=self.valid_key,
            raw_cube=self.valid_cube,
            num_rotors_to_make=self.num_rotors_to_make,
            rotors_to_use=self.rotors_to_use,
        )

        self.assertEqual(result1, result2)


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


class TestPadChunkWithRandPadSymbols(unittest.TestCase):
    @patch("cubigma.utils.random")
    def test_pad_chunk_with_empty_input(self, mock_randint):
        with self.assertRaises(ValueError) as context:
            _pad_chunk_with_rand_pad_symbols("")
        self.assertIn("Chunk cannot be empty", str(context.exception))
        mock_randint.assert_not_called()

    @patch("random.randint")
    def test_pad_chunk_with_one_length_input(self, mock_randint):
        mock_randint.side_effect = [0, 1, 2]
        result = _pad_chunk_with_rand_pad_symbols("A")
        self.assertEqual(result, "A\x07\x16\x06")

    @patch("random.randint")
    def test_pad_chunk_with_two_length_input(self, mock_randint):
        mock_randint.side_effect = [2, 1]
        result = _pad_chunk_with_rand_pad_symbols("AB")
        self.assertEqual(result, "AB\x06\x16")

    @patch("random.randint")
    def test_pad_chunk_with_three_length_input(self, mock_randint):
        mock_randint.side_effect = [0]
        result = _pad_chunk_with_rand_pad_symbols("ABC")
        self.assertEqual(result, "ABC\x07")

    @patch("random.randint")
    def test_pad_chunk_with_full_length_input(self, mock_randint):
        result = _pad_chunk_with_rand_pad_symbols("ABCD")
        self.assertEqual(result, "ABCD")
        mock_randint.assert_not_called()


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
        )

        # Call the function
        key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography = (
            parse_arguments()
        )

        # Assertions
        self.assertEqual(key_phrase, "test_key")
        self.assertEqual(mode, "encrypt")
        self.assertEqual(message, "test_message")
        self.assertEqual(cube_length, 5)
        self.assertEqual(num_rotors_to_make, 3)
        self.assertEqual(rotors_to_use, [1, 2, 3])
        self.assertTrue(should_use_steganography)
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
        )

        # Call the function
        key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography = (
            parse_arguments(mode="decrypt")
        )

        # Assertions
        self.assertEqual(key_phrase, "test_key")
        self.assertEqual(mode, "decrypt")
        self.assertEqual(message, "test_encrypted_message")  # Message is empty because it isn't provided
        self.assertEqual(cube_length, 4)
        self.assertEqual(num_rotors_to_make, 2)
        self.assertEqual(rotors_to_use, [0, 1])
        self.assertFalse(should_use_steganography)
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["cryptid", "message"])
    @patch("cubigma.utils._read_and_validate_config")
    def test_parse_arguments_invalid_mode(self, mock_read_and_validate_config, mock_input):
        """Test parse_arguments function with an invalid mode."""
        mock_read_and_validate_config.return_value = (0, 0, [], "invalid_mode", False)

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
            quartet_to_index("123🇬🇵", self.symbols)  # Symbol is not present in cube.txt


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
        raw_salt = "foo"
        salt = raw_salt.encode("utf-8")
        key, returned_salt = strengthen_key(key_phrase, salt=salt)
        salt_decoded_bytes = base64.b64decode(returned_salt)
        found_plaintext_salt = salt_decoded_bytes.decode("utf-8")

        self.assertIsInstance(key, str)
        self.assertIsInstance(returned_salt, str)
        self.assertEqual("D8QofLkX4FdRLdsq69mAr+Y9g2nfwPqnc7EX4kZaY3c=", key)
        self.assertEqual("Zm9v", returned_salt)
        self.assertEqual(len(returned_salt), 4)
        self.assertEqual(raw_salt, found_plaintext_salt)

    def test_key_generation_without_salt(self):
        """Test that strengthen_key generates a key and random salt when no salt is provided."""
        key_phrase = "test-key"
        key, salt = strengthen_key(key_phrase)

        self.assertIsInstance(key, str)
        self.assertIsInstance(salt, str)
        self.assertEqual(len(salt), 24)

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
        salt1 = "foo1".encode("utf-8")
        salt2 = "foo2".encode("utf-8")
        key1, _ = strengthen_key(key_phrase, salt=salt1)
        key2, _ = strengthen_key(key_phrase, salt=salt2)

        self.assertNotEqual(key1, key2)

    def test_key_length_parameter(self):
        """Test that the derived key length matches the specified key_length."""
        key_phrase = "test-key"
        key_length = 64
        returned_key, _ = strengthen_key(key_phrase, key_length=key_length)
        key_decoded_bytes = base64.b64decode(returned_key)

        self.assertEqual(len(key_decoded_bytes), key_length)

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
