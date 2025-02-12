# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from copy import deepcopy
from unittest.mock import patch
import unittest

from cubigma.utils import LENGTH_OF_TRIO
from cubigma.utils import (
    _find_symbol,
    _get_flat_index,
    _get_prefix_order_number_trio,
    _get_random_noise_chunk,
    _is_valid_coord,
    _pad_chunk_with_rand_pad_symbols,
    _read_and_validate_config,
    _rotate_2d_array,
    _shuffle_cube_with_key_phrase,
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


class TestGetPrefixOrderNumberTrio(unittest.TestCase):
    @staticmethod
    def _fake_shuffle(input_list):
        return reversed(input_list)

    @patch("cubigma.utils.get_non_deterministically_random_shuffled")
    def test_valid_order_number(self, mock_shuffle):
        """Test that a valid single-digit order number returns a trio of symbols including the order number."""
        # Arrange
        order_number = 5
        mock_shuffle.side_effect = self._fake_shuffle
        orig_pad_symbols = ["\x07", "\x06", str(order_number)]
        expected_result = f"{str(order_number)}\x06\x07"

        # Act
        result = _get_prefix_order_number_trio(order_number)

        # Assert
        self.assertEqual(len(result), LENGTH_OF_TRIO, "Resulting string does not have 3 characters")
        self.assertIn(str(order_number), result, f"Order number {order_number} is not in the result")
        self.assertEqual(result, expected_result)
        mock_shuffle.assert_called_once_with(orig_pad_symbols)

    @patch("cubigma.utils.get_non_deterministically_random_shuffled")
    def test_invalid_order_number(self, mock_shuffle):
        """Test that an invalid order number raises an assertion error."""
        with self.assertRaises(AssertionError):
            _get_prefix_order_number_trio(10)  # Not a single-digit number
        mock_shuffle.assert_not_called()

        with self.assertRaises(AssertionError):
            _get_prefix_order_number_trio(-1)  # Negative number
        mock_shuffle.assert_not_called()

        with self.assertRaises(AssertionError):
            _get_prefix_order_number_trio(123)  # Multiple digits
        mock_shuffle.assert_not_called()


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

    @patch("cubigma.utils.get_non_deterministically_random_int")
    @patch("cubigma.utils.get_non_deterministically_random_shuffled")
    def test_output_length(self, mock_shuffle, mock_randint):
        """Test that the function output has the correct length."""
        # Arrange
        mock_randint.side_effect = [0, 0, 0, 1, 1, 1]  # Mock coordinates
        expected_symbols_1 = ["\x15", "A", "N"]
        expected_symbols_2 = ["B", "L", "A"]
        expected_result = "BLA"
        mock_shuffle.return_value = expected_symbols_2

        # act
        result = _get_random_noise_chunk(self.rotor)

        # Assert
        self.assertEqual(result, expected_result)
        mock_shuffle.assert_called_once_with(expected_symbols_1)
        assert mock_randint.call_count == 6


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


class TestPadChunkWithRandPadSymbols(unittest.TestCase):
    @patch("cubigma.utils.get_non_deterministically_random_int")
    def test_pad_chunk_with_empty_input(self, mock_randint):
        with self.assertRaises(ValueError) as context:
            _pad_chunk_with_rand_pad_symbols("")
        self.assertIn("Chunk cannot be empty", str(context.exception))
        mock_randint.assert_not_called()

    @patch("cubigma.utils.get_non_deterministically_random_int")
    def test_pad_chunk_with_one_length_input(self, mock_randint):
        mock_randint.side_effect = [0, 1]
        result = _pad_chunk_with_rand_pad_symbols("A")
        self.assertEqual(result, "A\x07\x16")
        assert mock_randint.call_count == 2

    @patch("cubigma.utils.get_non_deterministically_random_int")
    def test_pad_chunk_with_two_length_input(self, mock_randint):
        expected_max_num = 2
        mock_randint.return_value = expected_max_num
        result = _pad_chunk_with_rand_pad_symbols("AB")
        self.assertEqual(result, "AB\x06")
        mock_randint.assert_called_once_with(0, expected_max_num)

    @patch("cubigma.utils.get_non_deterministically_random_int")
    def test_pad_chunk_with_three_length_input(self, mock_randint):
        mock_randint.side_effect = [0]
        result = _pad_chunk_with_rand_pad_symbols("ABC")
        self.assertEqual(result, "ABC")
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

    @patch("cubigma.utils.shuffle_for_input")
    def test_consistent_shuffling_with_same_key(self, mock_shuffle):
        """Test that shuffling with the same key gives consistent results."""
        # Assert
        expected_cube = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        random_cube = ["b", "a", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        mock_shuffle.return_value = random_cube

        # Act
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")

        # Assert
        self.assertEqual(shuffled_1, shuffled_2)
        assert mock_shuffle.call_count == 2
        mock_shuffle.assert_any_call(f"{self.key_phrase_1}|{42}", expected_cube)

    @patch("cubigma.utils.shuffle_for_input")
    def test_different_keys_produce_different_results(self, mock_shuffle):
        """Test that shuffling with different keys gives different results."""
        # Assert
        expected_cube = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        random_cube_1 = ["b", "a", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        random_cube_2 = ["c", "a", "b", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        mock_shuffle.side_effect = [random_cube_1, random_cube_2]

        # Act
        shuffled_1 = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")
        shuffled_2 = _shuffle_cube_with_key_phrase(self.key_phrase_2, deepcopy(self.orig_cube), "42")

        # Assert
        self.assertNotEqual(shuffled_1, shuffled_2)
        assert mock_shuffle.call_count == 2
        mock_shuffle.assert_any_call(f"{self.key_phrase_1}|{42}", expected_cube)
        mock_shuffle.assert_any_call(f"{self.key_phrase_2}|{42}", expected_cube)

    @patch("cubigma.utils.shuffle_for_input")
    def test_structure_preserved(self, mock_shuffle):
        """Test that the structure of the cube is preserved after shuffling."""
        # Assert
        expected_cube = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        random_cube = ["b", "a", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        mock_shuffle.return_value = random_cube

        # Act
        shuffled = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")

        # Assert
        self.assertEqual(len(shuffled), len(self.orig_cube))
        mock_shuffle.assert_called_once_with(f"{self.key_phrase_1}|{42}", expected_cube)
        for orig_outer, shuffled_outer in zip(self.orig_cube, shuffled):
            # Ensure the second-level list length is preserved
            self.assertEqual(len(shuffled_outer), len(orig_outer))
            for orig_inner, shuffled_inner in zip(orig_outer, shuffled_outer):
                # Ensure the third-level list length is preserved
                self.assertEqual(len(shuffled_inner), len(orig_inner))

    @patch("cubigma.utils.shuffle_for_input")
    def test_no_side_effects(self, mock_shuffle):
        """Test that the original cube is not modified by the function."""
        # Assert
        expected_cube = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        random_cube = ["b", "a", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        mock_shuffle.return_value = random_cube
        orig_cube_copy = deepcopy(self.orig_cube)

        # Act
        _ = _shuffle_cube_with_key_phrase(self.key_phrase_1, deepcopy(self.orig_cube), "42")

        # Assert
        self.assertEqual(self.orig_cube, orig_cube_copy)
        mock_shuffle.assert_called_once_with(f"{self.key_phrase_1}|{42}", expected_cube)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
