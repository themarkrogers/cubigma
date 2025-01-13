# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from contextlib import redirect_stderr
from unittest.mock import patch
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
    prepare_cuboid_with_key_phrase,
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
    _split_key_into_parts,
)


# Testing Private Functions


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
        test_cuboid = [
            expected_return_value[3],
            expected_return_value[2],
            expected_return_value[1],
            expected_return_value[0],
        ]

        # Act
        result = _move_letter_to_center(test_symbol, test_cuboid)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((2, 0, 1), (2, 2, 2), test_cuboid)

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
        test_cuboid = [expected_return_value[2], expected_return_value[1], expected_return_value[0]]

        # Act
        result = _move_letter_to_center(test_symbol, test_cuboid)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((1, 2, 2), (1, 1, 1), test_cuboid)


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
        test_cuboid = [expected_return_value[2], expected_return_value[1], expected_return_value[0]]

        # Act
        result = _move_letter_to_front(test_symbol, test_cuboid)

        # Assert
        self.assertEqual(expected_return_value, result)
        mock_move_symbol_in_3d_grid.assert_called_once_with((1, 2, 2), (0, 0, 0), test_cuboid)


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
        """
        Set up reusable test data for the tests.
        """
        self.sanitized_key_phrase = "TESTKEY"
        self.prepared_playfair_cuboid = [
            [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "_"]],
        ]
        self.num_rotors = 3

    @patch("random.seed")
    @patch("cubigma.utils._split_key_into_parts")
    @patch("cubigma.utils._move_letter_to_center")
    def test_generate_rotors_valid(self, mock_move_letter, mock_split_key, mock_seed):
        """
        Test that the function generates the correct number of rotors with deterministic output.
        """
        mock_seed.return_value = None
        mock_split_key.return_value = ["TE", "ST", "KEY"]
        mock_move_letter.side_effect = lambda symbol, inner_rotor: inner_rotor  # Mocking as identity for simplicity

        result = generate_rotors(self.sanitized_key_phrase, self.prepared_playfair_cuboid, self.num_rotors)

        self.assertEqual(len(result), self.num_rotors, "Should create the correct number of rotors.")
        for rotor in result:
            self.assertEqual(rotor, self.prepared_playfair_cuboid, "Each rotor should match the mock-adjusted input.")

    def test_generate_rotors_empty_key(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors("", self.prepared_playfair_cuboid, self.num_rotors)

    def test_generate_rotors_null_key(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors(None, self.prepared_playfair_cuboid, self.num_rotors)

    def test_generate_rotors_non_string_key(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors(420, self.prepared_playfair_cuboid, self.num_rotors)

    def test_generate_rotors_zero_rotors(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors(self.sanitized_key_phrase, self.prepared_playfair_cuboid, 0)

    def test_generate_rotors_null_rotors(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors(self.sanitized_key_phrase, self.prepared_playfair_cuboid, None)

    def test_generate_rotors_non_number_num_rotors(self):
        """
        Test that the function raises an error when the key is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors(self.sanitized_key_phrase, self.prepared_playfair_cuboid, "3")

    def test_generate_rotors_too_many_rotors(self):
        """
        Test that the function raises an error when the playfair cuboid is invalid.
        """
        with self.assertRaises(ValueError):
            generate_rotors("1234", self.prepared_playfair_cuboid, 5)

    def test_generate_rotors_invalid_cuboid_string(self):
        """
        Test that the function raises an error when the playfair cuboid is invalid.
        """
        invalid_cuboid = "InvalidCuboid"
        with self.assertRaises(ValueError, msg="Should raise a TypeError if the cuboid is not a 3D list."):
            generate_rotors(self.sanitized_key_phrase, invalid_cuboid, self.num_rotors)

    def test_generate_rotors_invalid_cuboid_number(self):
        """
        Test that the function raises an error when the playfair cuboid is invalid.
        """
        invalid_cuboid = [
            [[4, "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "_"]],
        ]
        with self.assertRaises(ValueError, msg="Should raise a TypeError if the cuboid is not a 3D list."):
            generate_rotors(self.sanitized_key_phrase, invalid_cuboid, self.num_rotors)

    def test_generate_rotors_invalid_cuboid_2d_array(self):
        """
        Test that the function raises an error when the playfair cuboid is invalid.
        """
        invalid_cuboid = [["ABC", "DEF", "GHI"], ["JKL", "MNO", "PQR"], ["STU", "VWX", "YZ_"]]
        with self.assertRaises(ValueError, msg="Should raise a TypeError if the cuboid is not a 3D list."):
            generate_rotors(self.sanitized_key_phrase, invalid_cuboid, self.num_rotors)

    @patch("random.seed")
    def test_generate_rotors_different_seeds(self, mock_seed):
        """
        Test that the function generates different outputs for different keys.
        """
        mock_seed.return_value = None
        cuboid = [
            [["K", "E", "Y"], ["_", "A", "B"], ["C", "D", "F"]],
            [["G", "H", "I"], ["J", "L", "M"], ["N", "O", "P"]],
            [["Q", "R", "S"], ["T", "U", "V"], ["W", "X", "Z"]],
        ]
        key_phrase_1 = "KEY_A"
        key_phrase_2 = "KEY_B"

        result1 = generate_rotors(key_phrase_1, cuboid, self.num_rotors)
        result2 = generate_rotors(key_phrase_2, cuboid, self.num_rotors)

        self.assertNotEqual(result1, result2, "Different keys should produce different rotors.")


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
            point_1, point_2, point_3, point_4,
            self.num_blocks, self.lines_per_block, self.symbols_per_line,
            self.key_phrase, self.num_quartets_encoded
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
                point_1, point_2, point_3, point_4,
                self.num_blocks, self.lines_per_block, self.symbols_per_line,
                self.key_phrase, self.num_quartets_encoded
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
            point_1, point_2, point_3, point_4,
            self.num_blocks, self.lines_per_block, self.symbols_per_line,
            "key1", self.num_quartets_encoded
        )

        result_2 = get_opposite_corners(
            point_1, point_2, point_3, point_4,
            self.num_blocks, self.lines_per_block, self.symbols_per_line,
            "key2", self.num_quartets_encoded
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
        self.rotor = [[['A', 'B', 'C'], ['D', 'E', 'F'], ['G', 'H', 'I']]]

    @patch("cubigma.utils._pad_chunk_with_rand_pad_symbols")
    @patch("cubigma.utils._get_random_noise_chunk")
    @patch("cubigma.utils._get_prefix_order_number_quartet")
    def test_pad_chunk_even_length(self, mock_get_prefix_order_number_quartet, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols):
        # Arrange
        mock_get_prefix_order_number_quartet.return_value = "ORDR"
        mock_get_random_noise_chunk.return_value = "XXXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "TEST"
        expected_result = 'ORDRTESTXXXXXXXXXXXX'
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
    def test_pad_chunk_short_length(self, mock_get_prefix_order_number_quartet, mock_get_random_noise_chunk, mock_pad_chunk_with_rand_pad_symbols):
        # Arrange
        mock_get_prefix_order_number_quartet.return_value = "ORDR"
        mock_get_random_noise_chunk.return_value = "XXXX"
        mock_pad_chunk_with_rand_pad_symbols.side_effect = lambda padded_chunk: padded_chunk + "P"
        test_chunk = "TES"
        expected_result = 'ORDRTESPXXXXXXXXXXXX'
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


class TestParseArguments(unittest.TestCase):
    @patch("builtins.print")
    @patch("builtins.input", side_effect=["encrypt", "test_key", "This is a test message"])
    def test_interactive_mode_encrypt(self, mock_print, mock_input):
        """Test interactive mode for encryption."""
        with patch("sys.argv", ["script_name"]):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "encrypt")
            self.assertEqual(message, "This is a test message")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["decrypt", "test_key", "EncryptedMessage"])
    def test_interactive_mode_decrypt(self, mock_print, mock_input):
        """Test interactive mode for decryption."""
        with patch("sys.argv", ["script_name"]):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "decrypt")
            self.assertEqual(message, "EncryptedMessage")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["both", "test_key", "EncryptedMessage"])
    def test_interactive_mode_both(self, mock_print, mock_input):
        """Test interactive mode for decryption."""
        with patch("sys.argv", ["script_name"]):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "both")
            self.assertEqual(message, "EncryptedMessage")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["rawr", "again", "encrypt", "test_key", "EncryptedMessage"])
    def test_interactive_mode_invalid(self, mock_print, mock_input):
        """Test interactive mode for decryption."""
        with patch("sys.argv", ["script_name"]):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "encrypt")
            self.assertEqual(message, "EncryptedMessage")

    def test_command_line_encrypt(self):
        """Test command-line arguments for encryption."""
        with patch(
            "sys.argv", ["script_name", "--key_phrase", "test_key", "--clear_text_message", "This is a test message"]
        ):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "encrypt")
            self.assertEqual(message, "This is a test message")

    def test_command_line_decrypt(self):
        """Test command-line arguments for decryption."""
        with patch("sys.argv", ["script_name", "--key_phrase", "test_key", "--encrypted_message", "EncryptedMessage"]):
            key_phrase, mode, message = parse_arguments()
            self.assertEqual(key_phrase, "test_key")
            self.assertEqual(mode, "decrypt")
            self.assertEqual(message, "EncryptedMessage")

    def test_command_line_error_both_messages(self):
        """Test error when both --clear_text_message and --encrypted_message are provided."""
        with patch(
            "sys.argv",
            [
                "script_name",
                "--key_phrase",
                "test_key",
                "--clear_text_message",
                "Text",
                "--encrypted_message",
                "Encrypted",
            ],
        ):
            # Redirect stderr to silence the argparse error message
            with self.assertRaises(SystemExit) as cm:
                with open(os.devnull, "w") as devnull, redirect_stderr(devnull):
                    parse_arguments()
            self.assertEqual(cm.exception.code, 2)  # argparse exits with code 2 for errors

    def test_command_line_error_key_and_no_message(self):
        """Test error when both --clear_text_message and --encrypted_message are provided."""
        with patch("sys.argv", ["script_name", "--key_phrase", "test_key"]):
            with self.assertRaises(SystemExit) as cm:
                with open(os.devnull, "w") as devnull, redirect_stderr(devnull):
                    parse_arguments()
            self.assertEqual(cm.exception.code, 2)  # argparse exits with code 2 for errors

    def test_command_line_error_clear_message_and_no_key(self):
        """Test error when both --clear_text_message and --encrypted_message are provided."""
        with patch("sys.argv", ["script_name", "--clear_text_message", "Text"]):
            with self.assertRaises(SystemExit) as cm:
                with open(os.devnull, "w") as devnull, redirect_stderr(devnull):
                    parse_arguments()
            self.assertEqual(cm.exception.code, 2)  # argparse exits with code 2 for errors

    def test_command_line_error_encrypted_message_and_no_key(self):
        """Test error when both --clear_text_message and --encrypted_message are provided."""
        with patch("sys.argv", ["script_name", "--encrypted_message", "Text"]):
            with self.assertRaises(SystemExit) as cm:
                with open(os.devnull, "w") as devnull, redirect_stderr(devnull):
                    parse_arguments()
            self.assertEqual(cm.exception.code, 2)  # argparse exits with code 2 for errors

    @patch("builtins.print")
    def test_no_arguments_provided(self, mock_print):
        """Test behavior when no arguments are provided."""
        with patch("sys.argv", ["script_name"]), patch("builtins.input", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                # User interrupts interactive mode
                with open(os.devnull, "w") as devnull, redirect_stderr(devnull):
                    parse_arguments()


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


class TestPrepareCuboidWithKeyPhrase(unittest.TestCase):
    def setUp(self):
        # Initial playfair cuboid setup
        self.playfair_cuboid = [
            [
                ['A', 'B', 'C'],
                ['D', 'E', 'F'],
                ['G', 'H', 'I']
            ],
            [
                ['J', 'K', 'L'],
                ['M', 'N', 'O'],
                ['P', 'Q', 'R']
            ],
            [
                ['S', 'T', 'U'],
                ['V', 'W', 'X'],
                ['Y', 'Z', '-']
            ]
        ]

    def test_valid_key_phrase(self):
        key_phrase = "HELLO"
        expected_cuboid = [
            [
                ['H', 'E', 'L'],
                ['O', 'A', 'B'],
                ['C', 'D', 'F']
            ],
            [
                ['G', 'I', 'J'],
                ['K', 'M', 'N'],
                ['P', 'Q', 'R']
            ],
            [
                ['S', 'T', 'U'],
                ['V', 'W', 'X'],
                ['Y', 'Z', '-']
            ]
        ]
        result = prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)
        self.assertEqual(result, expected_cuboid)

    def test_short_key_phrase(self):
        key_phrase = "AB"
        with self.assertRaises(AssertionError) as context:
            prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)
        self.assertEqual(str(context.exception), "Key phrase must be at least 3 characters long")

    def test_key_phrase_with_duplicates(self):
        key_phrase = "BALLOON"
        expected_cuboid = [
            [
                ['B', 'A', 'L'],
                ['O', 'N', 'C'],
                ['D', 'E', 'F']
            ],
            [
                ['G', 'H', 'I'],
                ['J', 'K', 'M'],
                ['P', 'Q', 'R']
            ],
            [
                ['S', 'T', 'U'],
                ['V', 'W', 'X'],
                ['Y', 'Z', '-']
            ]
        ]
        result = prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)
        self.assertEqual(result, expected_cuboid)

    def test_empty_key_phrase(self):
        key_phrase = ""
        with self.assertRaises(AssertionError) as context:
            prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)
        self.assertEqual(str(context.exception), "Key phrase must be at least 3 characters long")


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
