# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, mock_open, MagicMock
import json
import os
import unittest

from cubigma.generate_reflectors import generate_reflector, read_reflector_from_file, write_reflector_to_file, main


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


class TestReadReflectorFromFile(unittest.TestCase):

    def setUp(self):
        self.cube_size = 3
        self.output_dir = "reflectors"
        self.file_name = f"reflector_{self.cube_size}.json"
        self.file_path = os.path.join(self.output_dir, self.file_name)

    @patch("os.path.exists")
    def test_file_not_found(self, mock_exists):
        """Test that FileNotFoundError is raised if the reflector file doesn't exist."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError) as context:
            read_reflector_from_file(self.cube_size, self.output_dir)
        self.assertIn(f"Reflector file for cube size {self.cube_size} not found", str(context.exception))

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_successful_read(self, mock_open_func, mock_exists):
        """Test successful reading and rehydrating of the reflector."""
        # Arrange
        mock_exists.return_value = True
        compressed_reflector = [[0, 1], [2, 3], [4, 5]]
        mock_open_func().read.return_value = json.dumps(compressed_reflector)
        expected_reflector = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}

        # Act
        result = read_reflector_from_file(self.cube_size, self.output_dir)

        # Assert
        self.assertEqual(result, expected_reflector)
        mock_open_func.assert_any_call(self.file_path, "r")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_json_format(self, mock_open_func, mock_exists):
        """Test that a JSONDecodeError is raised for invalid JSON format."""
        mock_exists.return_value = True
        mock_open_func().read.return_value = "invalid json"

        with self.assertRaises(json.JSONDecodeError):
            read_reflector_from_file(self.cube_size, self.output_dir)

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_empty_file(self, mock_open_func, mock_exists):
        """Test that an empty file returns an empty reflector."""
        mock_exists.return_value = True
        mock_open_func().read.return_value = json.dumps([])

        result = read_reflector_from_file(self.cube_size, self.output_dir)
        self.assertEqual(result, {})
        mock_open_func.assert_any_call(self.file_path, "r")


class TestWriteReflectorToFile(unittest.TestCase):

    @patch("builtins.print")
    @patch("os.makedirs")
    @patch("builtins.open")
    @patch("json.dump")
    @patch("math.comb")
    @patch("cubigma.generate_reflectors.generate_reflector")
    def test_write_reflector_to_file(self, mock_generate_reflector, mock_comb, mock_json_dump, mock_open_file, mock_makedirs, mock_print):
        # Setup test data
        cube_sizes = [3, 4]
        sanitized_key_phrase = "test_key"
        output_dir = "test_reflectors"

        # Mock the behavior of math.comb and generate_reflector
        mock_comb.side_effect = lambda n, r: 10  # Arbitrary number of unique quartets
        mock_generate_reflector.side_effect = lambda key, num: {i: i + 1 for i in range(num)}

        # Call the function
        write_reflector_to_file(cube_sizes, sanitized_key_phrase, output_dir)

        # Verify that os.makedirs was called with the correct arguments
        mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)

        # Verify that math.comb and generate_reflector were called correctly
        mock_comb.assert_any_call(27, 4)  # Cube size 3 -> 3^3 = 27
        mock_comb.assert_any_call(64, 4)  # Cube size 4 -> 4^3 = 64

        mock_generate_reflector.assert_any_call(sanitized_key_phrase, 10)
        mock_generate_reflector.assert_any_call(sanitized_key_phrase, 10)
        mock_open_file.assert_any_call(f"{output_dir}/reflector_{cube_sizes[0]}.json", 'w', encoding='utf-8')
        mock_open_file.assert_any_call(f"{output_dir}/reflector_{cube_sizes[-1]}.json", 'w', encoding='utf-8')

        # Verify files were written correctly
        expected_files = [
            os.path.join(output_dir, "reflector_3.json"),
            os.path.join(output_dir, "reflector_4.json"),
        ]
        self.assertEqual(mock_open_file.call_count, len(expected_files))
        for call_args, expected_file in zip(mock_open_file.call_args_list, expected_files):
            self.assertEqual(call_args[0][0], expected_file)
            self.assertEqual(call_args[0][1], "w")
            self.assertEqual(call_args[1]["encoding"], "utf-8")

        # Verify json.dump was called with compressed reflectors
        compressed_reflector_1 = [(k, v) for k, v in {i: i + 1 for i in range(10)}.items() if k <= v]
        self.assertEqual(mock_json_dump.call_args_list[0][0][0], compressed_reflector_1)
        mock_print.assert_any_call(f'Reflector for cube size {cube_sizes[0]} saved to {output_dir}/reflector_{cube_sizes[0]}.json')
        mock_print.assert_any_call(f'Reflector for cube size {cube_sizes[-1]} saved to {output_dir}/reflector_{cube_sizes[-1]}.json')

    @patch("builtins.print")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_directory_creation(self, mock_builtin_open, mock_makedirs, mock_print):
        # Arrange
        test_cube_size = 2
        test_dir = "another_dir"
        write_reflector_to_file([test_cube_size], "key", test_dir)

        # Assert
        mock_makedirs.assert_called_once_with(test_dir, exist_ok=True)
        mock_builtin_open.assert_called_once_with(f"{test_dir}/reflector_{test_cube_size}.json", 'w', encoding='utf-8')
        mock_print.assert_called_once_with(f'Reflector for cube size {test_cube_size} saved to {test_dir}/reflector_{test_cube_size}.json')


class TestMain(unittest.TestCase):
    @patch("cubigma.generate_reflectors.write_reflector_to_file")
    @patch("cubigma.generate_reflectors.strengthen_key")
    def test_main(self, mock_strengthen_key, mock_write_reflector_to_file):
        # Arrange
        expected_cube_sizes = [5, 6, 7, 8, 9, 10, 11]
        expected_key_phrase = "This is not the key_phrase that was used to create the files stored in git ;)"
        expected_key = "foo_key"
        mock_strengthen_key.return_value = expected_key, "bar_salt"

        # Act
        main()

        # Assert
        mock_strengthen_key.assert_called_once_with(expected_key_phrase, salt=None)
        mock_write_reflector_to_file.assert_called_once_with(expected_cube_sizes, expected_key)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
