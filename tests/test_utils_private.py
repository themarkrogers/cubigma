# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from copy import deepcopy
from unittest.mock import patch
import unittest

from cubigma.utils import (
    NOISE_SYMBOL,
    LENGTH_OF_QUARTET,
    # get_chars_for_coordinates,
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
    _rotate_2d_array,
    _shuffle_cube_with_key_phrase,
    _split_key_into_parts,
)


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


class TestPadChunkWithRandPadSymbols(unittest.TestCase):
    @patch("cubigma.utils.get_non_deterministically_random_int")
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


class TestReadAndValidateConfig(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "LENGTH_OF_CUBE": 7,
            "NUMBER_OF_ROTORS_TO_GENERATE": 10,
            "ROTORS_TO_USE": [1, 2, 3],
            "ENCRYPT_OR_DECRYPT": "ENCRYPT",
            "ALSO_USE_STEGANOGRAPHY": True,
            "PLUGBOARD": ["AB", "CD"],
        }

    @patch("cubigma.utils.read_config")
    def test_valid_config(self, mock_read_config):
        mock_read_config.return_value = self.valid_config
        result = _read_and_validate_config()
        self.assertEqual(result, (7, 10, [1, 2, 3], "ENCRYPT", True, ["AB", "CD"]))

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
            "ROTORS_TO_USE (in config.json) all rotor values must be between 0 & the number of rotors generated",
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

    @patch("cubigma.utils.read_config")
    def test_missing_plugboard(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        del invalid_config["PLUGBOARD"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("PLUGBOARD not found in config.json", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_plugboard(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["PLUGBOARD"] = "['AB', 'CD', 'EF']"
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("PLUGBOARD (in config.json) must be a list of symbol pairs", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_plugboard_values_1(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["PLUGBOARD"] = ["AB", 1, "CD", 2]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn("PLUGBOARD (in config.json) contains a non-string value at index: 1", str(context.exception))

    @patch("cubigma.utils.read_config")
    def test_incorrect_plugboard_values_2(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["PLUGBOARD"] = ["ABC", "DE"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "PLUGBOARD (in config.json) all plugboard values must be pairs of symbols.",
            str(context.exception),
        )

    @patch("cubigma.utils.read_config")
    def test_incorrect_plugboard_values_3(self, mock_read_config):
        invalid_config = self.valid_config.copy()
        invalid_config["PLUGBOARD"] = ["AB", "BC"]
        mock_read_config.return_value = invalid_config
        with self.assertRaises(ValueError) as context:
            _read_and_validate_config()
        self.assertIn(
            "PLUGBOARD (in config.json) all plugboard symbols must be unique",
            str(context.exception),
        )


class TestRotate2DArray(unittest.TestCase):
    def setUp(self):
        # Common test cases
        self.square_matrix = [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]]
        self.rectangular_matrix = [["1", "2", "3"], ["4", "5", "6"]]
        self.empty_matrix = []
        self.single_element_matrix = [["x"]]

    def test_clockwise_rotation_square(self):
        result = _rotate_2d_array(self.square_matrix, 1)
        expected = [["g", "d", "a"], ["h", "e", "b"], ["i", "f", "c"]]
        self.assertEqual(result, expected)

    def test_counterclockwise_rotation_square(self):
        result = _rotate_2d_array(self.square_matrix, -1)
        expected = [["c", "f", "i"], ["b", "e", "h"], ["a", "d", "g"]]
        self.assertEqual(result, expected)

    def test_clockwise_rotation_rectangular(self):
        result = _rotate_2d_array(self.rectangular_matrix, 1)
        expected = [["4", "1"], ["5", "2"], ["6", "3"]]
        self.assertEqual(result, expected)

    def test_counterclockwise_rotation_rectangular(self):
        result = _rotate_2d_array(self.rectangular_matrix, -1)
        expected = [["3", "6"], ["2", "5"], ["1", "4"]]
        self.assertEqual(result, expected)

    def test_empty_matrix(self):
        result = _rotate_2d_array(self.empty_matrix, 1)
        self.assertEqual(result, [])

    def test_single_element_matrix(self):
        result_clockwise = _rotate_2d_array(self.single_element_matrix, 1)
        result_counterclockwise = _rotate_2d_array(self.single_element_matrix, -1)
        self.assertEqual(result_clockwise, [["x"]])
        self.assertEqual(result_counterclockwise, [["x"]])

    def test_invalid_direction(self):
        with self.assertRaises(ValueError):
            _rotate_2d_array(self.square_matrix, 0)
        with self.assertRaises(ValueError):
            _rotate_2d_array(self.square_matrix, 2)


class TestShuffleCubeWithKeyPhrase(unittest.TestCase):
    def setUp(self):
        """Set up reusable test data."""
        self.key_phrase_1 = "securekey1"
        self.key_phrase_2 = "differentkey"

        self.orig_cube = [[["a", "b", "c"], ["d", "e", "f"]], [["g", "h", "i"], ["j", "k", "l"]]]

    def test_consistent_shuffling_with_same_key(self):
        """Test that shuffling with the same key gives consistent results."""
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
        self.assertEqual(shuffled_1, shuffled_2)

    def test_different_keys_produce_different_results(self):
        """Test that shuffling with different keys gives different results."""
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_2, deepcopy(self.orig_cube), "42")
        self.assertNotEqual(shuffled_1, shuffled_2)

    def test_structure_preserved(self):
        """Test that the structure of the cube is preserved after shuffling."""
        shuffled = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
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
        _ = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
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


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
